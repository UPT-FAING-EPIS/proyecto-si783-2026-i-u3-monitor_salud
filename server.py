#!/usr/bin/env python3
"""Monitor de Salud DB — Flask + PostgreSQL + Multi-datasource."""

import os, re, threading, time, logging, configparser, secrets, hashlib, json
from datetime import datetime, timedelta
from pathlib import Path

try:
    import psutil
    _proc = psutil.Process()
    _PSUTIL = True
except Exception:
    psutil = None; _proc = None; _PSUTIL = False

import psycopg2, psycopg2.extras
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from db_connection import (
    get_monitor_conn, release_conn, build_dsn,
    connect_to_datasource, test_datasource, load_config
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("monitor")

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True

BASE_DIR = Path(__file__).parent
_initialized = threading.Event()
_cache: dict = {}          # {ds_id: {"metrics": ..., "error": ..., "ts": ...}}
_cache_lock = threading.Lock()
_APP_VERSION = "1.0.0"
_START_TIME = datetime.now()

AUTH_PUBLIC_PATHS = {
    "/",
    "/api/health",
    "/api/config",
    "/api/login",
    "/api/register",
    "/api/me",
    "/api/logout",
    "/static/style.css",
    "/static/dashboard.js",
}

# ── API Key helpers ───────────────────────────────────────────────────────────

def generate_api_key() -> tuple[str, str]:
    """Returns (raw_token, hashed_token). Store only the hash."""
    raw = "dhm_" + secrets.token_urlsafe(32)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def resolve_bearer_user() -> dict | None:
    """If request has a valid Bearer API key, return {username, role}."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer dhm_"):
        return None
    raw = auth_header[len("Bearer "):].strip()
    hashed = hash_api_key(raw)
    conn = get_monitor_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT ak.id, au.username, au.role
            FROM api_keys ak
            JOIN auth_users au ON ak.user_id = au.id
            WHERE ak.key_hash = %s AND ak.active = TRUE AND au.active = TRUE
        """, (hashed,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE api_keys SET last_used = NOW() WHERE id = %s", (row["id"],))
            conn.commit()
        cur.close()
        return dict(row) if row else None
    finally:
        release_conn(conn)


# Intent detection for chatbox (keyword → handler)
CHATBOX_INTENTS = [
    (["cpu", "procesador"], "cpu"),
    (["memoria", "ram", "memory"], "memory"),
    (["disco", "disk", "almacenamiento"], "disk"),
    (["conexi", "connect"], "connections"),
    (["cache", "hit ratio", "buffer"], "cache"),
    (["alerta", "alert", "warn", "critico", "critical"], "alerts"),
    (["estado", "status", "salud", "health"], "status"),
    (["base", "datasource", "fuente"], "datasources"),
    (["uptime", "tiempo activo", "actividad"], "uptime"),
    (["hola", "hi", "hello", "buenas"], "greet"),
    (["ayuda", "help", "que puedes", "qué puedes"], "help"),
]

FILE_PROFILE_DEFS = {
    "postgresql": [
        {"key": "config", "label": "Configuración", "description": "postgresql.conf, pg_hba.conf", "paths": ["{config_dir}/postgresql.conf", "{config_dir}/pg_hba.conf", "{config_dir}/pg_ident.conf"]},
        {"key": "data", "label": "Datos", "description": "Directorio de datos y WAL", "paths": ["{data_dir}", "{data_dir}/pg_wal"]},
        {"key": "log", "label": "Logs", "description": "Registros del servidor", "paths": ["{log_dir}"]},
        {"key": "backup", "label": "Respaldo", "description": "Directorio de backups", "paths": ["{backup_dir}"]},
    ],
    "mysql": [
        {"key": "config", "label": "Configuración", "description": "my.cnf / mysqld.cnf", "paths": ["{config_dir}/my.cnf", "{config_dir}/mysql.conf.d/mysqld.cnf"]},
        {"key": "data", "label": "Datos", "description": "Directorio de datos", "paths": ["{data_dir}"]},
        {"key": "log", "label": "Logs", "description": "Error log y logs del motor", "paths": ["{log_dir}"]},
        {"key": "backup", "label": "Respaldo", "description": "Directorio de backups", "paths": ["{backup_dir}"]},
    ],
    "mariadb": [
        {"key": "config", "label": "Configuración", "description": "50-server.cnf / my.cnf", "paths": ["{config_dir}/my.cnf", "{config_dir}/mariadb.conf.d/50-server.cnf"]},
        {"key": "data", "label": "Datos", "description": "Directorio de datos", "paths": ["{data_dir}"]},
        {"key": "log", "label": "Logs", "description": "Registro de errores", "paths": ["{log_dir}"]},
        {"key": "backup", "label": "Respaldo", "description": "Directorio de backups", "paths": ["{backup_dir}"]},
    ],
    "sqlserver": [
        {"key": "config", "label": "Configuración", "description": "Archivos de instancia y configuración", "paths": ["{config_dir}"]},
        {"key": "data", "label": "Datos", "description": "Archivos MDF/NDF", "paths": ["{data_dir}"]},
        {"key": "log", "label": "Logs", "description": "Log de error y trazas", "paths": ["{log_dir}"]},
        {"key": "backup", "label": "Respaldo", "description": "Backups", "paths": ["{backup_dir}"]},
    ],
    "mongodb": [
        {"key": "config", "label": "Configuración", "description": "mongod.conf", "paths": ["{config_dir}/mongod.conf"]},
        {"key": "data", "label": "Datos", "description": "dbPath", "paths": ["{data_dir}"]},
        {"key": "log", "label": "Logs", "description": "Log de MongoDB", "paths": ["{log_dir}"]},
        {"key": "backup", "label": "Respaldo", "description": "Backups", "paths": ["{backup_dir}"]},
    ],
}

# ── Config helpers ────────────────────────────────────────────────────────────

def cfg_int(section, key, fallback):
    try: return load_config().getint(section, key, fallback=fallback)
    except: return fallback

def cfg_bool(section, key, fallback=True):
    try: return load_config().getboolean(section, key, fallback=fallback)
    except: return fallback


def bootstrap_admin_credentials() -> tuple[str, str]:
    cfg = load_config()
    user = os.environ.get("APP_BOOTSTRAP_USER", cfg.get("auth", "username", fallback="admin"))
    password = os.environ.get("APP_BOOTSTRAP_PASSWORD", cfg.get("auth", "password", fallback="Admin2026!"))
    return user, password


def ensure_auth_ready() -> None:
    if not _initialized.is_set():
        init_db(retries=1, delay=0.0)


def authenticate_user(username: str, password: str) -> dict | None:
    ensure_auth_ready()
    conn = get_monitor_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT id, username, password_hash, role, active
            FROM auth_users
            WHERE username = %s
            """,
            (username,),
        )
        row = cur.fetchone()
        cur.close()
        if not row or not row.get("active"):
            return None
        if not check_password_hash(row["password_hash"], password):
            return None
        return dict(row)
    finally:
        release_conn(conn)


def seed_default_user(conn) -> None:
    username, password = bootstrap_admin_credentials()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO auth_users (username, password_hash, role, active)
        VALUES (%s, %s, %s, TRUE)
        ON CONFLICT (username) DO NOTHING
        """,
        (username, generate_password_hash(password), "admin"),
    )
    cur.execute(
        """
        INSERT INTO auth_users (username, password_hash, role, active)
        VALUES (%s, %s, %s, TRUE)
        ON CONFLICT (username) DO NOTHING
        """,
        ("ariana", generate_password_hash("123456"), "viewer"),
    )
    conn.commit()
    cur.close()


def current_username() -> str | None:
    return session.get("user")


def current_role() -> str:
    return str(session.get("role", "viewer"))


def is_admin() -> bool:
    return current_role() == "admin"


def is_logged_in() -> bool:
    return bool(session.get("user"))


@app.before_request
def require_login():
    if request.path in AUTH_PUBLIC_PATHS:
        return None
    if request.path.startswith("/static/"):
        return None
    if request.path.startswith("/api/") and not is_logged_in():
        # Try Bearer API key auth
        bearer_user = resolve_bearer_user()
        if bearer_user:
            session["user"] = bearer_user["username"]
            session["role"] = bearer_user["role"]
            return None
        return {"error": "No autenticado"}, 401
    return None


def _default_file_roots(ds: dict) -> dict:
    tipo = (ds.get("tipo_db") or "postgresql").lower()
    cfg = load_config()
    if tipo == "postgresql":
        return {
            "config_dir": cfg.get("files", "postgresql_config_dir", fallback="/etc/postgresql/15/main"),
            "data_dir": cfg.get("files", "postgresql_data_dir", fallback="/var/lib/postgresql/15/main"),
            "log_dir": cfg.get("files", "postgresql_log_dir", fallback="/var/log/postgresql"),
            "backup_dir": cfg.get("files", "postgresql_backup_dir", fallback="/var/backups/postgresql"),
        }
    if tipo in ("mysql", "mariadb"):
        return {
            "config_dir": cfg.get("files", "mysql_config_dir", fallback="/etc/mysql"),
            "data_dir": cfg.get("files", "mysql_data_dir", fallback="/var/lib/mysql"),
            "log_dir": cfg.get("files", "mysql_log_dir", fallback="/var/log/mysql"),
            "backup_dir": cfg.get("files", "mysql_backup_dir", fallback="/var/backups/mysql"),
        }
    if tipo in ("sqlserver", "mssql"):
        return {
            "config_dir": cfg.get("files", "sqlserver_config_dir", fallback="C:/Program Files/Microsoft SQL Server"),
            "data_dir": cfg.get("files", "sqlserver_data_dir", fallback="C:/Program Files/Microsoft SQL Server/MSSQL/Data"),
            "log_dir": cfg.get("files", "sqlserver_log_dir", fallback="C:/Program Files/Microsoft SQL Server/MSSQL/Log"),
            "backup_dir": cfg.get("files", "sqlserver_backup_dir", fallback="C:/Backups/SQLServer"),
        }
    if tipo == "mongodb":
        return {
            "config_dir": cfg.get("files", "mongodb_config_dir", fallback="/etc"),
            "data_dir": cfg.get("files", "mongodb_data_dir", fallback="/var/lib/mongodb"),
            "log_dir": cfg.get("files", "mongodb_log_dir", fallback="/var/log/mongodb"),
            "backup_dir": cfg.get("files", "mongodb_backup_dir", fallback="/var/backups/mongodb"),
        }
    return {"config_dir": ".", "data_dir": ".", "log_dir": ".", "backup_dir": "."}


def _safe_stat_path(path: str) -> dict:
    try:
        p = Path(path)
        if not p.exists():
            return {"exists": False, "kind": "missing", "size_mb": 0.0, "modified_at": None, "entries": 0}
        if p.is_file():
            st = p.stat()
            return {
                "exists": True,
                "kind": "file",
                "size_mb": round(st.st_size / 1024 / 1024, 3),
                "modified_at": datetime.fromtimestamp(st.st_mtime).isoformat(),
                "entries": 1,
            }
        total_size = 0
        count = 0
        for child in p.rglob("*"):
            try:
                if child.is_file():
                    total_size += child.stat().st_size
                    count += 1
            except Exception:
                continue
        st = p.stat()
        return {
            "exists": True,
            "kind": "directory",
            "size_mb": round(total_size / 1024 / 1024, 3),
            "modified_at": datetime.fromtimestamp(st.st_mtime).isoformat(),
            "entries": count,
        }
    except Exception as exc:
        return {"exists": False, "kind": "error", "error": str(exc), "size_mb": 0.0, "modified_at": None, "entries": 0}


def get_file_profile_defs(tipo_db: str) -> list[dict]:
    return FILE_PROFILE_DEFS.get((tipo_db or "postgresql").lower(), FILE_PROFILE_DEFS["postgresql"])


def build_file_inventory(ds: dict, selected_types: list[str] | None = None) -> list[dict]:
    roots = _default_file_roots(ds)
    profiles = get_file_profile_defs(ds.get("tipo_db"))
    selected = {t.lower() for t in (selected_types or []) if t}
    if selected:
        profiles = [p for p in profiles if p["key"] in selected]

    inventory = []
    for profile in profiles:
        for raw_path in profile.get("paths", []):
            path = raw_path.format(**roots)
            stat_info = _safe_stat_path(path)
            inventory.append({
                "datasource_id": ds.get("id"),
                "datasource_name": ds.get("nombre"),
                "tipo_db": ds.get("tipo_db"),
                "file_type": profile["key"],
                "label": profile["label"],
                "description": profile["description"],
                "path": path,
                **stat_info,
            })
    return inventory

# ── DB Init ───────────────────────────────────────────────────────────────────


INIT_SQL = [
    # 1. Tablas nuevas (si no existen)
    """CREATE TABLE IF NOT EXISTS auth_users (
        id            SERIAL PRIMARY KEY,
        username      VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role          VARCHAR(30)  NOT NULL DEFAULT 'user',
        active        BOOLEAN      NOT NULL DEFAULT TRUE,
        created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
        last_login    TIMESTAMPTZ
    )""",
    """CREATE TABLE IF NOT EXISTS datasources (
        id         SERIAL PRIMARY KEY,
        nombre     VARCHAR(100) NOT NULL,
        tipo_db    VARCHAR(20)  NOT NULL DEFAULT 'postgresql',
        host       VARCHAR(255) NOT NULL,
        puerto     INTEGER      NOT NULL DEFAULT 5432,
        usuario    VARCHAR(100) NOT NULL,
        password   TEXT         NOT NULL DEFAULT '',
        database   VARCHAR(100) NOT NULL,
        activa     BOOLEAN      NOT NULL DEFAULT TRUE,
        owner_username VARCHAR(100) NOT NULL DEFAULT 'hashira',
        created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS health_snapshots (
        id                SERIAL PRIMARY KEY,
        datasource_id     INTEGER,
        captured_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        max_connections   INTEGER NOT NULL DEFAULT 0,
        threads_connected INTEGER NOT NULL DEFAULT 0,
        threads_running   INTEGER NOT NULL DEFAULT 0,
        connection_pct    REAL    NOT NULL DEFAULT 0,
        qps               REAL    NOT NULL DEFAULT 0,
        slow_queries      INTEGER NOT NULL DEFAULT 0,
        cache_hit_ratio   REAL    NOT NULL DEFAULT 0,
        db_size_mb        REAL    NOT NULL DEFAULT 0,
        cpu_pct           REAL    NOT NULL DEFAULT 0,
        mem_pct           REAL    NOT NULL DEFAULT 0,
        status            VARCHAR(20) NOT NULL DEFAULT 'OK'
    )""",
    """CREATE TABLE IF NOT EXISTS alert_log (
        id            SERIAL PRIMARY KEY,
        datasource_id INTEGER,
        alerted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        severity      VARCHAR(20) NOT NULL DEFAULT 'INFO',
        metric_name   VARCHAR(100) NOT NULL DEFAULT '',
        metric_value  VARCHAR(50) NOT NULL DEFAULT '',
        threshold     VARCHAR(100) NOT NULL DEFAULT '',
        message       TEXT NOT NULL DEFAULT ''
    )""",

    # 2. Migración: columnas que pueden faltar en BD existente
    "ALTER TABLE health_snapshots ADD COLUMN IF NOT EXISTS datasource_id INTEGER",
    "ALTER TABLE health_snapshots ADD COLUMN IF NOT EXISTS cache_hit_ratio REAL NOT NULL DEFAULT 0",
    "ALTER TABLE health_snapshots ADD COLUMN IF NOT EXISTS db_size_mb REAL NOT NULL DEFAULT 0",
    "ALTER TABLE health_snapshots ADD COLUMN IF NOT EXISTS cpu_pct REAL NOT NULL DEFAULT 0",
    "ALTER TABLE health_snapshots ADD COLUMN IF NOT EXISTS mem_pct REAL NOT NULL DEFAULT 0",
    "ALTER TABLE health_snapshots ADD COLUMN IF NOT EXISTS qps REAL NOT NULL DEFAULT 0",
    "ALTER TABLE health_snapshots ADD COLUMN IF NOT EXISTS slow_queries INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE alert_log ADD COLUMN IF NOT EXISTS datasource_id INTEGER",
    "ALTER TABLE auth_users ADD COLUMN IF NOT EXISTS role VARCHAR(30) NOT NULL DEFAULT 'user'",
    "ALTER TABLE auth_users ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE auth_users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
    "ALTER TABLE auth_users ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ",
    "ALTER TABLE datasources ADD COLUMN IF NOT EXISTS owner_username VARCHAR(100) NOT NULL DEFAULT 'hashira'",
    # 3. Tablas de integración
    """CREATE TABLE IF NOT EXISTS api_keys (
        id          SERIAL PRIMARY KEY,
        user_id     INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
        name        VARCHAR(100) NOT NULL DEFAULT 'Mi API Key',
        key_hash    VARCHAR(64)  NOT NULL UNIQUE,
        active      BOOLEAN      NOT NULL DEFAULT TRUE,
        created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
        last_used   TIMESTAMPTZ
    )""",
    """CREATE TABLE IF NOT EXISTS skill_files (
        id          SERIAL PRIMARY KEY,
        user_id     INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
        name        VARCHAR(100) NOT NULL,
        description TEXT         NOT NULL DEFAULT '',
        content     TEXT         NOT NULL DEFAULT '',
        active      BOOLEAN      NOT NULL DEFAULT TRUE,
        created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
    )""",
    # 4. Índices
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_auth_users_username ON auth_users (username)",
    "CREATE INDEX IF NOT EXISTS idx_snap_ds  ON health_snapshots (datasource_id, captured_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_alert_ds ON alert_log        (datasource_id, alerted_at  DESC)",
    "CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys (key_hash)",
    "CREATE INDEX IF NOT EXISTS idx_skill_files_user ON skill_files (user_id)",

]


def init_db(retries=10, delay=6.0):
    for attempt in range(retries):
        try:
            conn = get_monitor_conn()
            cur  = conn.cursor()
            for stmt in INIT_SQL:
                try:
                    cur.execute(stmt)
                    conn.commit()
                except Exception as e:
                    log.warning("init_db stmt skip: %s", str(e)[:120])
                    conn.rollback()
            # Seed datasource principal si no hay ninguno
            seed_default_user(conn)
            bootstrap_owner = bootstrap_admin_credentials()[0]
            cur.execute("SELECT COUNT(*) FROM datasources")
            if cur.fetchone()[0] == 0:
                cfg = load_config()
                cur.execute("""
                    INSERT INTO datasources (nombre, tipo_db, host, puerto, usuario, password, database, owner_username)
                    VALUES (%s,'postgresql',%s,%s,%s,%s,%s,%s)
                """, (
                    "Monitor Principal (VM)",
                    cfg.get("postgresql","host",fallback="localhost"),
                    cfg.getint("postgresql","port",fallback=5432),
                    cfg.get("postgresql","user",fallback="monitor"),
                    cfg.get("postgresql","password",fallback=""),
                    cfg.get("postgresql","database",fallback="db_health_monitor"),
                    bootstrap_owner,
                ))
                conn.commit()
            cur.execute("UPDATE datasources SET owner_username = %s WHERE owner_username IS NULL OR owner_username = ''", (bootstrap_owner,))
            conn.commit()
            cur.close()
            release_conn(conn)
            log.info("Base de datos inicializada OK.")
            _initialized.set()
            return True
        except Exception as e:
            log.warning("init_db intento %d/%d: %s", attempt+1, retries, e)
            if attempt < retries-1: time.sleep(delay)
    log.error("No se pudo inicializar la BD tras %d intentos.", retries)
    _initialized.set()
    return False

# ── Recolección de métricas ───────────────────────────────────────────────────

def collect_pg_metrics(ds: dict) -> dict:
    conn = connect_to_datasource(ds, timeout=8)
    cur = conn.cursor()

    cur.execute("""
        SELECT blks_hit, blks_read, numbackends,
               pg_database_size(datname) AS sz
        FROM pg_stat_database WHERE datname = current_database()
    """)
    row = cur.fetchone() or (0,0,0,0)
    blks_hit, blks_read, num_backends, db_size_bytes = row
    total_blks = (blks_hit or 0) + (blks_read or 0)
    cache_hit  = round((blks_hit/total_blks)*100, 2) if total_blks else 99.9

    cur.execute("SELECT setting::int FROM pg_settings WHERE name='max_connections'")
    max_conn = (cur.fetchone() or [100])[0]

    cur.execute("SELECT count(*) FROM pg_stat_activity WHERE state='active' AND pid<>pg_backend_pid()")
    active = (cur.fetchone() or [0])[0]

    cur.execute("SELECT count(*) FROM pg_stat_activity WHERE wait_event_type IS NOT NULL AND pid<>pg_backend_pid()")
    waiting = (cur.fetchone() or [0])[0]

    cur.execute("SELECT EXTRACT(EPOCH FROM (now() - pg_postmaster_start_time()))::bigint")
    uptime_seconds = int((cur.fetchone() or [0])[0] or 0)

    cur.close(); conn.close()

    db_mb   = round((db_size_bytes or 0)/1024/1024, 2)
    conn_pct= round(min(99.9, num_backends/max_conn*100), 2) if max_conn else 0

    # psutil
    cpu_pct = mem_pct = disk_used_pct = 0.0
    disk_free_gb = 0.0
    host_processes = 0
    try:
        if _PSUTIL:
            cpu_pct = psutil.cpu_percent(interval=None)
            mem_pct = psutil.virtual_memory().percent
            disk = psutil.disk_usage(str(BASE_DIR))
            disk_used_pct = disk.percent
            disk_free_gb = round(disk.free / 1024 / 1024 / 1024, 2)
            host_processes = len(psutil.pids())
    except Exception: pass

    status = "OK"
    if conn_pct >= 90 or cache_hit < 70: status = "CRITICAL"
    elif conn_pct >= 70 or cache_hit < 85: status = "WARNING"

    return {
        "datasource_id":    ds["id"],
        "tipo_db":          "postgresql",
        "timestamp":        datetime.now().isoformat(),
        "max_connections":  max_conn,
        "threads_connected":num_backends,
        "threads_running":  active,
        "threads_waiting":  waiting,
        "connection_pct":   conn_pct,
        "qps":              0.0,
        "slow_queries":     0,
        "cache_hit_ratio":  cache_hit,
        "db_size_mb":       db_mb,
        "cpu_pct":          cpu_pct,
        "mem_pct":          mem_pct,
        "disk_used_pct":    disk_used_pct,
        "disk_free_gb":     disk_free_gb,
        "host_processes":   host_processes,
        "uptime_seconds":   uptime_seconds,
        "status":           status,
    }


def collect_mysql_metrics(ds: dict) -> dict:
    conn = connect_to_datasource(ds, timeout=8)
    cur  = conn.cursor()

    # Variables globales de estado
    cur.execute("SHOW GLOBAL STATUS")
    status_vars = {row[0]: row[1] for row in cur.fetchall()}

    # max_connections
    cur.execute("SHOW GLOBAL VARIABLES LIKE 'max_connections'")
    max_conn = int((cur.fetchone() or [None, 100])[1])

    threads_connected = int(status_vars.get("Threads_connected", 0))
    threads_running   = int(status_vars.get("Threads_running",   0))
    slow_queries      = int(status_vars.get("Slow_queries",       0))
    uptime_seconds    = int(status_vars.get("Uptime", 0))

    # Procesos en espera
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.processlist
        WHERE command != 'Sleep'
    """)
    threads_waiting = int((cur.fetchone() or [0])[0])

    # InnoDB cache hit ratio
    pool_reads    = int(status_vars.get("Innodb_buffer_pool_reads",         0))
    pool_requests = int(status_vars.get("Innodb_buffer_pool_read_requests", 1))
    if pool_requests > 0:
        cache_hit = round((1 - pool_reads / pool_requests) * 100, 2)
    else:
        cache_hit = 99.9
    cache_hit = max(0.0, min(100.0, cache_hit))

    # Tamaño de la base de datos en MB
    cur.execute("""
        SELECT COALESCE(SUM(data_length + index_length), 0) / 1024 / 1024
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
    """)
    db_mb = round(float((cur.fetchone() or [0])[0]), 2)

    cur.close(); conn.close()

    conn_pct = round(min(99.9, threads_connected / max_conn * 100), 2) if max_conn else 0

    # psutil
    cpu_pct = mem_pct = disk_used_pct = 0.0
    disk_free_gb = 0.0
    host_processes = 0
    try:
        if _PSUTIL:
            cpu_pct = psutil.cpu_percent(interval=None)
            mem_pct = psutil.virtual_memory().percent
            disk = psutil.disk_usage(str(BASE_DIR))
            disk_used_pct = disk.percent
            disk_free_gb = round(disk.free / 1024 / 1024 / 1024, 2)
            host_processes = len(psutil.pids())
    except Exception: pass

    status = "OK"
    if conn_pct >= 90 or cache_hit < 70: status = "CRITICAL"
    elif conn_pct >= 70 or cache_hit < 85: status = "WARNING"

    return {
        "datasource_id":    ds["id"],
        "tipo_db":          "mysql",
        "timestamp":        datetime.now().isoformat(),
        "max_connections":  max_conn,
        "threads_connected":threads_connected,
        "threads_running":  threads_running,
        "threads_waiting":  threads_waiting,
        "connection_pct":   conn_pct,
        "qps":              0.0,
        "slow_queries":     slow_queries,
        "cache_hit_ratio":  cache_hit,
        "db_size_mb":       db_mb,
        "cpu_pct":          cpu_pct,
        "mem_pct":          mem_pct,
        "disk_used_pct":    disk_used_pct,
        "disk_free_gb":     disk_free_gb,
        "host_processes":   host_processes,
        "uptime_seconds":   uptime_seconds,
        "status":           status,
    }


def collect_mariadb_metrics(ds: dict) -> dict:
    """MariaDB es compatible con MySQL — reutiliza la misma función."""
    m = collect_mysql_metrics(ds)
    m["tipo_db"] = "mariadb"
    return m


def collect_sqlserver_metrics(ds: dict) -> dict:
    conn = connect_to_datasource(ds, timeout=8)
    cur  = conn.cursor()

    # Max connections
    cur.execute("SELECT value_in_use FROM sys.configurations WHERE name = 'max connections'")
    max_conn_val = int((cur.fetchone() or [0])[0])
    max_conn = max_conn_val if max_conn_val > 0 else 32767

    # Conexiones activas y en espera
    cur.execute("""
        SELECT
            COUNT(*),
            SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END),
            SUM(CASE WHEN wait_type IS NOT NULL THEN 1 ELSE 0 END)
        FROM sys.dm_exec_sessions
        WHERE is_user_process = 1
    """)
    row = cur.fetchone() or (0, 0, 0)
    threads_connected = int(row[0] or 0)
    threads_running   = int(row[1] or 0)
    threads_waiting   = int(row[2] or 0)

    # Cache hit ratio (Buffer Manager)
    cur.execute("""
        SELECT
            MAX(CASE WHEN counter_name = 'Buffer cache hit ratio'
                     THEN CAST(cntr_value AS FLOAT) END),
            MAX(CASE WHEN counter_name = 'Buffer cache hit ratio base'
                     THEN CAST(cntr_value AS FLOAT) END)
        FROM sys.dm_os_performance_counters
        WHERE counter_name IN ('Buffer cache hit ratio', 'Buffer cache hit ratio base')
          AND object_name LIKE '%Buffer Manager%'
    """)
    row = cur.fetchone() or (0, 1)
    hit, base = (float(row[0] or 0)), (float(row[1] or 1))
    cache_hit = round((hit / base) * 100, 2) if base else 99.9
    cache_hit = max(0.0, min(100.0, cache_hit))

    # Tamaño de la base de datos actual en MB
    cur.execute("""
        SELECT CAST(SUM(size) * 8.0 / 1024 AS FLOAT)
        FROM sys.master_files
        WHERE database_id = DB_ID()
    """)
    db_mb = round(float((cur.fetchone() or [0])[0] or 0), 2)

    # Slow queries (queries con duración > 1s)
    cur.execute("""
        SELECT COUNT(*)
        FROM sys.dm_exec_requests r
        CROSS APPLY sys.dm_exec_sql_text(r.sql_handle)
        WHERE r.total_elapsed_time > 1000
    """)
    slow_queries = int((cur.fetchone() or [0])[0])

    cur.execute("SELECT DATEDIFF(SECOND, sqlserver_start_time, SYSDATETIME()) FROM sys.dm_os_sys_info")
    uptime_seconds = int((cur.fetchone() or [0])[0] or 0)

    cur.close(); conn.close()

    conn_pct = round(min(99.9, threads_connected / max_conn * 100), 2) if max_conn else 0

    cpu_pct = mem_pct = disk_used_pct = 0.0
    disk_free_gb = 0.0
    host_processes = 0
    try:
        if _PSUTIL:
            cpu_pct = psutil.cpu_percent(interval=None)
            mem_pct = psutil.virtual_memory().percent
            disk = psutil.disk_usage(str(BASE_DIR))
            disk_used_pct = disk.percent
            disk_free_gb = round(disk.free / 1024 / 1024 / 1024, 2)
            host_processes = len(psutil.pids())
    except Exception: pass

    status = "OK"
    if conn_pct >= 90 or cache_hit < 70: status = "CRITICAL"
    elif conn_pct >= 70 or cache_hit < 85: status = "WARNING"

    return {
        "datasource_id":    ds["id"],
        "tipo_db":          "sqlserver",
        "timestamp":        datetime.now().isoformat(),
        "max_connections":  max_conn,
        "threads_connected":threads_connected,
        "threads_running":  threads_running,
        "threads_waiting":  threads_waiting,
        "connection_pct":   conn_pct,
        "qps":              0.0,
        "slow_queries":     slow_queries,
        "cache_hit_ratio":  cache_hit,
        "db_size_mb":       db_mb,
        "cpu_pct":          cpu_pct,
        "mem_pct":          mem_pct,
        "disk_used_pct":    disk_used_pct,
        "disk_free_gb":     disk_free_gb,
        "host_processes":   host_processes,
        "uptime_seconds":   uptime_seconds,
        "status":           status,
    }


def collect_mongodb_metrics(ds: dict) -> dict:
    from db_connection import _MONGO_OK
    if not _MONGO_OK:
        raise RuntimeError("Driver MongoDB no instalado. Añade pymongo a requirements.txt.")
    import pymongo as _pymongo

    uri_auth = ""
    if ds.get("usuario"):
        from urllib.parse import quote_plus as _qp
        uri_auth = f"{_qp(ds['usuario'])}:{_qp(ds['password'])}@"
    uri = f"mongodb://{uri_auth}{ds['host']}:{ds['puerto']}/{ds['database']}"
    client = _pymongo.MongoClient(
        uri,
        serverSelectionTimeoutMS=8000,
        connectTimeoutMS=8000,
        socketTimeoutMS=8000,
    )
    try:
        srv = client.admin.command("serverStatus")

        conns       = srv.get("connections", {})
        current     = int(conns.get("current",   0))
        available   = int(conns.get("available", 1000))
        max_conn    = current + available

        # WiredTiger cache hit ratio
        wt          = srv.get("wiredTiger", {}).get("cache", {})
        reads_into  = int(wt.get("pages read into cache",        1))
        reads_req   = int(wt.get("pages requested from the cache", 1))
        cache_hit   = round((1 - reads_into / max(reads_req, 1)) * 100, 2)
        cache_hit   = max(0.0, min(100.0, cache_hit))

        # Tamaño de la BD
        db_stats    = client[ds["database"]].command("dbStats")
        db_mb       = round(db_stats.get("dataSize", 0) / 1024 / 1024, 2)

        # Operaciones activas
        cur_op      = client.admin.command("currentOp")
        inprog      = cur_op.get("inprog", [])
        running     = sum(1 for op in inprog if not op.get("waitingForLock", False))
        waiting     = sum(1 for op in inprog if     op.get("waitingForLock", False))

        conn_pct = round(min(99.9, current / max_conn * 100), 2) if max_conn else 0

        cpu_pct = mem_pct = disk_used_pct = 0.0
        disk_free_gb = 0.0
        host_processes = 0
        try:
            if _PSUTIL:
                cpu_pct = psutil.cpu_percent(interval=None)
                mem_pct = psutil.virtual_memory().percent
            disk = psutil.disk_usage(str(BASE_DIR))
            disk_used_pct = disk.percent
            disk_free_gb = round(disk.free / 1024 / 1024 / 1024, 2)
            host_processes = len(psutil.pids())
        except Exception: pass

        status = "OK"
        if conn_pct >= 90 or cache_hit < 70: status = "CRITICAL"
        elif conn_pct >= 70 or cache_hit < 85: status = "WARNING"

        return {
            "datasource_id":    ds["id"],
            "tipo_db":          "mongodb",
            "timestamp":        datetime.now().isoformat(),
            "max_connections":  max_conn,
            "threads_connected":current,
            "threads_running":  running,
            "threads_waiting":  waiting,
            "connection_pct":   conn_pct,
            "qps":              0.0,
            "slow_queries":     0,
            "cache_hit_ratio":  cache_hit,
            "db_size_mb":       db_mb,
            "cpu_pct":          cpu_pct,
            "mem_pct":          mem_pct,
            "disk_used_pct":    disk_used_pct,
            "disk_free_gb":     disk_free_gb,
            "host_processes":   host_processes,
            "uptime_seconds":   int(srv.get("uptime", 0)),
            "status":           status,
        }
    finally:
        client.close()


def save_snapshot(m: dict):
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO health_snapshots
              (datasource_id, max_connections, threads_connected, threads_running,
               connection_pct, qps, slow_queries, cache_hit_ratio,
               db_size_mb, cpu_pct, mem_pct, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (m["datasource_id"], m["max_connections"], m["threads_connected"],
              m["threads_running"], m["connection_pct"], m["qps"],
              m["slow_queries"], m["cache_hit_ratio"], m["db_size_mb"],
              m["cpu_pct"], m["mem_pct"], m["status"]))
        cur.execute("""
            DELETE FROM health_snapshots
            WHERE datasource_id=%s AND id NOT IN (
              SELECT id FROM health_snapshots
              WHERE datasource_id=%s ORDER BY id DESC LIMIT 5000
            )
        """, (m["datasource_id"], m["datasource_id"]))
        conn.commit(); cur.close()
    finally:
        release_conn(conn)

def evaluate_alerts(m: dict, cfg) -> list:
    def t(k,d): return cfg.getfloat("thresholds",k,fallback=d)
    alerts = []
    checks = [
        ("connection_pct",  m["connection_pct"],  t("connections_warning",70), t("connections_critical",90), "Conexiones %",     False),
        ("cache_hit_ratio", m["cache_hit_ratio"],  t("cache_hit_warning",85),  t("cache_hit_critical",70),   "Cache Hit Ratio %", True),
        ("cpu_pct",         m["cpu_pct"],          t("cpu_warning",75),        t("cpu_critical",90),         "CPU %",            False),
        ("mem_pct",         m["mem_pct"],          t("mem_warning",80),        t("mem_critical",95),         "Memoria %",        False),
    ]
    for key, val, warn, crit, label, invert in checks:
        if invert:
            sev = "CRITICAL" if val < crit else "WARNING" if val < warn else None
        else:
            sev = "CRITICAL" if val >= crit else "WARNING" if val >= warn else None
        if sev:
            alerts.append({"severity":sev,"metric":label,"value":str(val),
                           "threshold":f"W={warn} C={crit}","ds_id":m["datasource_id"]})
    return alerts

def save_alerts(alerts: list, ds_id: int):
    if not alerts: return
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        for a in alerts:
            cur.execute("""
                INSERT INTO alert_log (datasource_id,severity,metric_name,metric_value,threshold,message)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (ds_id, a["severity"], a["metric"], a["value"], a["threshold"],
                  f"{a['metric']}={a['value']} | umbral:{a['threshold']}"))
        conn.commit(); cur.close()
    finally:
        release_conn(conn)

# ── Hilo de fondo ─────────────────────────────────────────────────────────────

def background_collector():
    log.info("Iniciando background_collector...")
    init_db()
    cfg = load_config()
    tick = 0
    if _PSUTIL:
        try: psutil.cpu_percent(interval=None)
        except: pass

    while True:
        try:
            conn = get_monitor_conn()
            cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM datasources WHERE activa=TRUE")
            sources = [dict(r) for r in cur.fetchall()]
            cur.close(); release_conn(conn)

            for ds in sources:
                ds_id = ds["id"]
                try:
                    tipo = (ds.get("tipo_db") or "postgresql").lower()
                    if tipo == "postgresql":
                        m = collect_pg_metrics(ds)
                    elif tipo == "mysql":
                        m = collect_mysql_metrics(ds)
                    elif tipo == "mariadb":
                        m = collect_mariadb_metrics(ds)
                    elif tipo in ("sqlserver", "mssql"):
                        m = collect_sqlserver_metrics(ds)
                    elif tipo == "mongodb":
                        m = collect_mongodb_metrics(ds)
                    else:
                        raise NotImplementedError(f"Tipo '{tipo}' no soportado aún.")
                    with _cache_lock:
                        _cache[ds_id] = {"metrics": m, "error": None,
                                         "ts": datetime.now().isoformat()}
                    tick += 1
                    if tick % 2 == 0:
                        save_snapshot(m)
                        alts = evaluate_alerts(m, cfg)
                        if alts: save_alerts(alts, ds_id)
                except Exception as e:
                    log.error("background_collector: %s", e)
        except Exception as e:
            log.error("background_collector: %s", e)

        interval = cfg_int("monitor", "refresh_interval", 10)
        time.sleep(interval)




def get_ds_by_id(ds_id: int) -> dict | None:
    username = current_username()
    if not username:
        return None
    conn = get_monitor_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if is_admin():
            cur.execute("SELECT * FROM datasources WHERE id=%s", (ds_id,))
        else:
            cur.execute("SELECT * FROM datasources WHERE id=%s AND owner_username=%s", (ds_id, username))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    finally:
        release_conn(conn)


def get_owned_datasource_ids() -> set[int]:
    username = current_username()
    if not username:
        return set()
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        if is_admin():
            cur.execute("SELECT id FROM datasources")
        else:
            cur.execute("SELECT id FROM datasources WHERE owner_username=%s", (username,))
        rows = {row[0] for row in cur.fetchall()}
        cur.close()
        return rows
    finally:
        release_conn(conn)

# ── Rutas ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index(): return render_template("index.html")

@app.route("/api/health")
def api_health():
    started = _initialized.is_set()
    uptime = int((datetime.now() - _START_TIME).total_seconds())
    return jsonify({
        "status": "ok" if started else "starting",
        "version": _APP_VERSION,
        "uptime_seconds": uptime,
        "server_time": datetime.now().isoformat(),
    })


@app.route("/api/me")
def api_me():
    if not is_logged_in():
        return {"authenticated": False}, 401
    return {"authenticated": True, "user": session.get("user"), "role": session.get("role", "viewer")}


@app.route("/api/login", methods=["POST"])
def api_login():
    payload = request.get_json(silent=True) or request.form or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    user = authenticate_user(username, password)
    if not user:
        return {"ok": False, "error": "Usuario o contraseña inválidos"}, 401

    ensure_auth_ready()
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE auth_users SET last_login = NOW() WHERE id = %s", (user["id"],))
        conn.commit()
        cur.close()
    finally:
        release_conn(conn)

    session["user"] = user["username"]
    session["role"] = user.get("role", "user")
    return {"ok": True, "user": user["username"], "role": user.get("role", "user")}


@app.route("/api/register", methods=["POST"])
def api_register():
    payload = request.get_json(silent=True) or request.form or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    confirm = str(payload.get("confirm_password", payload.get("confirm", "")))

    if len(username) < 3:
        return {"ok": False, "error": "El usuario debe tener al menos 3 caracteres"}, 400
    if len(password) < 6:
        return {"ok": False, "error": "La contraseña debe tener al menos 6 caracteres"}, 400
    if password != confirm:
        return {"ok": False, "error": "Las contraseñas no coinciden"}, 400

    ensure_auth_ready()
    conn = get_monitor_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id FROM auth_users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            return {"ok": False, "error": "El usuario ya existe"}, 409

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO auth_users (username, password_hash, role, active)
            VALUES (%s, %s, %s, TRUE)
            RETURNING id
            """,
            (username, generate_password_hash(password), "user"),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return {"ok": True, "id": new_id, "user": username}
    finally:
        release_conn(conn)


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return {"ok": True}


@app.route("/api/file-types")
def api_file_types():
    ds_id = request.args.get("datasource_id", type=int)
    if ds_id:
        ds = get_ds_by_id(ds_id)
        if not ds:
            return {"error": "Datasource no encontrado"}, 404
        defs = get_file_profile_defs(ds.get("tipo_db"))
        return jsonify(defs)
    return jsonify({k: v for k, v in FILE_PROFILE_DEFS.items()})


@app.route("/api/files")
def api_files():
    ds_id = request.args.get("datasource_id", type=int)
    if not ds_id:
        return {"error": "datasource_id requerido"}, 400
    ds = get_ds_by_id(ds_id)
    if not ds:
        return {"error": "Datasource no encontrado"}, 404
    types_param = request.args.get("types", "")
    selected_types = [t.strip() for t in types_param.split(",") if t.strip()]
    files = build_file_inventory(ds, selected_types if selected_types else None)
    return jsonify({
        "datasource": {
            "id": ds["id"],
            "nombre": ds.get("nombre"),
            "tipo_db": ds.get("tipo_db"),
            "host": ds.get("host"),
            "puerto": ds.get("puerto"),
            "database": ds.get("database"),
        },
        "selected_types": selected_types,
        "files": files,
    })


@app.route("/api/files/read")
def api_files_read():
    ds_id = request.args.get("datasource_id", type=int)
    file_path = request.args.get("path", "").strip()
    if not ds_id or not file_path:
        return {"error": "datasource_id y path son requeridos"}, 400
    ds = get_ds_by_id(ds_id)
    if not ds:
        return {"error": "Datasource no encontrado"}, 404
    files = build_file_inventory(ds)
    allowed_paths = {f["path"] for f in files}
    if file_path not in allowed_paths:
        return {"error": "Acceso denegado a este archivo"}, 403
    try:
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return {"error": "Archivo no encontrado o inválido"}, 404
        st = p.stat()
        if st.st_size > 2 * 1024 * 1024:
            return {"error": "El archivo es demasiado grande (máximo 2 MB)"}, 400
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return jsonify({
            "path": file_path,
            "filename": p.name,
            "size_bytes": st.st_size,
            "content": content
        })
    except Exception as exc:
        return {"error": f"Error leyendo el archivo: {exc}"}, 500


# ── Datasources CRUD ──────────────────────────────────────────────────────────

@app.route("/api/datasources", methods=["GET"])
def api_ds_list():
    username = current_username()
    if not username:
        return jsonify([])
    conn = get_monitor_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if is_admin():
            cur.execute(
                """
                SELECT id,nombre,tipo_db,host,puerto,usuario,database,activa,created_at,owner_username
                FROM datasources
                ORDER BY id
                """
            )
        else:
            cur.execute(
                """
                SELECT id,nombre,tipo_db,host,puerto,usuario,database,activa,created_at,owner_username
                FROM datasources
                WHERE owner_username=%s
                ORDER BY id
                """,
                (username,),
            )
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        for r in rows:
            if hasattr(r.get("created_at"), "isoformat"):
                r["created_at"] = r["created_at"].isoformat()
            raw_active = r.get("activa")
            if isinstance(raw_active, str):
                r["activa"] = raw_active.strip().lower() in {"1", "true", "t", "yes", "y", "si", "sí"}
            else:
                r["activa"] = bool(raw_active)
            ds_id = r["id"]
            with _cache_lock:
                cached = _cache.get(ds_id, {})
            if not r["activa"]:
                r["status"] = "disabled"
            elif cached.get("metrics"):
                r["status"] = cached.get("metrics", {}).get("status", "unknown")
            elif cached.get("error"):
                r["status"] = "error"
            else:
                r["status"] = "unknown"
            r["last_error"] = cached.get("error")
            r["last_ts"]    = cached.get("ts")
        return jsonify(rows)
    finally:
        release_conn(conn)

@app.route("/api/datasources", methods=["POST"])
def api_ds_create():
    username = current_username()
    if not username:
        return {"error": "No autenticado"}, 401
    d = request.json or {}
    required = ["nombre","tipo_db","host","puerto","usuario","database"]
    missing = [f for f in required if not d.get(f)]
    if missing:
        return {"error": f"Faltan campos: {', '.join(missing)}"}, 400
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO datasources (nombre,tipo_db,host,puerto,usuario,password,database,activa,owner_username)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (d["nombre"], d["tipo_db"], d["host"], int(d["puerto"]),
              d["usuario"], d.get("password",""), d["database"],
              d.get("activa", True), username))
        new_id = cur.fetchone()[0]
        conn.commit(); cur.close()
        return {"id": new_id, "message": "Datasource creado."}, 201
    finally:
        release_conn(conn)


@app.route("/api/admin/overview")
def api_admin_overview():
    if not is_admin():
        return {"error": "No autorizado"}, 403
    conn = get_monitor_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, username, role, active, created_at, last_login FROM auth_users ORDER BY id")
        users = [dict(row) for row in cur.fetchall()]
        cur.execute("SELECT id, nombre, tipo_db, host, puerto, usuario, database, activa, owner_username, created_at FROM datasources ORDER BY id")
        datasources = [dict(row) for row in cur.fetchall()]
        cur.close()
        for row in users + datasources:
            for key in ("created_at", "last_login"):
                value = row.get(key)
                if hasattr(value, "isoformat"):
                    row[key] = value.isoformat()
        return jsonify({
            "counts": {"users": len(users), "datasources": len(datasources)},
            "users": users,
            "datasources": datasources,
        })
    finally:
        release_conn(conn)

@app.route("/api/datasources/<int:ds_id>", methods=["PUT"])
def api_ds_update(ds_id):
    if not get_ds_by_id(ds_id):
        return {"error": "No encontrado."}, 404
    d = request.json or {}
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        fields, vals = [], []
        for col in ["nombre","tipo_db","host","puerto","usuario","password","database","activa"]:
            if col in d:
                fields.append(f"{col}=%s")
                vals.append(int(d[col]) if col == "puerto" else d[col])
        if not fields:
            return {"error": "Sin campos para actualizar."}, 400
        vals.append(ds_id)
        cur.execute(f"UPDATE datasources SET {', '.join(fields)} WHERE id=%s", vals)
        if cur.rowcount == 0:
            return {"error": "No encontrado."}, 404
        conn.commit(); cur.close()
        return {"message": "Actualizado."}
    finally:
        release_conn(conn)

@app.route("/api/datasources/<int:ds_id>", methods=["DELETE"])
def api_ds_delete(ds_id):
    if not get_ds_by_id(ds_id):
        return {"error": "No encontrado."}, 404
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM datasources WHERE id=%s", (ds_id,))
        if cur.rowcount == 0:
            return {"error": "No encontrado."}, 404
        conn.commit(); cur.close()
        with _cache_lock:
            _cache.pop(ds_id, None)
        return {"message": "Eliminado."}
    finally:
        release_conn(conn)

@app.route("/api/datasources/<int:ds_id>/test", methods=["POST"])
def api_ds_test(ds_id):
    ds = get_ds_by_id(ds_id)
    if not ds:
        return {"error": "No encontrado."}, 404
    ok, ms, err = test_datasource(ds)
    return {
        "ok": ok,
        "latency_ms": ms,
        "error": err,
        "datasource": {
            "id": ds.get("id"),
            "nombre": ds.get("nombre"),
            "tipo_db": ds.get("tipo_db"),
            "host": ds.get("host"),
            "puerto": ds.get("puerto"),
            "database": ds.get("database"),
            "activa": bool(ds.get("activa")),
        },
    }

# ── Métricas y resumen ────────────────────────────────────────────────────────

@app.route("/api/metrics")
def api_metrics():
    ds_id = request.args.get("datasource_id", type=int)
    with _cache_lock:
        snap = dict(_cache)
    owned_ids = get_owned_datasource_ids()
    if ds_id:
        if ds_id not in owned_ids:
            return {"error": "Datasource no encontrado"}, 404
        entry = snap.get(ds_id)
        if not entry:
            return {"status": "loading"}, 202
        return jsonify(entry)
    # todos
    return jsonify({ds_id: value for ds_id, value in snap.items() if ds_id in owned_ids})

@app.route("/api/summary/global")
def api_summary_global():
    with _cache_lock:
        snap = dict(_cache)
    owned_ids = get_owned_datasource_ids()
    snap = {ds_id: value for ds_id, value in snap.items() if ds_id in owned_ids}
    total  = len(snap)
    online = sum(1 for v in snap.values() if not v.get("error") and v.get("metrics"))
    statuses = [((v.get("metrics") or {}).get("status")) for v in snap.values() if v.get("metrics")]
    statuses = [status for status in statuses if status]
    global_st = "CRITICAL" if "CRITICAL" in statuses else "WARNING" if "WARNING" in statuses else "OK"
    return jsonify({
        "total_datasources": total,
        "online": online,
        "offline": total - online,
        "global_status": global_st,
        "datasources": {
            ds_id: {"status": (v.get("metrics") or {}).get("status","unknown"),
                    "error":  v.get("error"), "ts": v.get("ts")}
            for ds_id, v in snap.items()
        }
    })

@app.route("/api/summary/<int:ds_id>")
def api_summary_ds(ds_id):
    if ds_id not in get_owned_datasource_ids():
        return {"status": "loading"}, 202
    with _cache_lock:
        entry = _cache.get(ds_id)
    if not entry:
        return {"status": "loading"}, 202
    return jsonify(entry)

@app.route("/api/history")
def api_history():
    ds_id = request.args.get("datasource_id", type=int)
    owned_ids = get_owned_datasource_ids()
    conn = get_monitor_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if ds_id:
            if ds_id not in owned_ids:
                return {"error": "Datasource no encontrado"}, 404
            cur.execute("""
                SELECT * FROM health_snapshots WHERE datasource_id=%s
                ORDER BY id DESC LIMIT 100
            """, (ds_id,))
        else:
            if owned_ids:
                cur.execute("SELECT * FROM health_snapshots WHERE datasource_id = ANY(%s) ORDER BY id DESC LIMIT 200", (list(owned_ids),))
            else:
                cur.execute("SELECT * FROM health_snapshots WHERE 1=0")
        rows = [dict(r) for r in reversed(cur.fetchall())]
        cur.close()
        for r in rows:
            if hasattr(r.get("captured_at"), "isoformat"):
                r["captured_at"] = r["captured_at"].isoformat()
        return jsonify(rows)
    finally:
        release_conn(conn)

@app.route("/api/alerts/history")
def api_alerts_history():
    ds_id = request.args.get("datasource_id", type=int)
    owned_ids = get_owned_datasource_ids()
    conn = get_monitor_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if ds_id:
            if ds_id not in owned_ids:
                return {"error": "Datasource no encontrado"}, 404
            cur.execute("""
                SELECT * FROM alert_log WHERE datasource_id=%s
                ORDER BY id DESC LIMIT 50
            """, (ds_id,))
        else:
            if owned_ids:
                cur.execute("SELECT * FROM alert_log WHERE datasource_id = ANY(%s) ORDER BY id DESC LIMIT 200", (list(owned_ids),))
            else:
                cur.execute("SELECT * FROM alert_log WHERE 1=0")
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        for r in rows:
            if hasattr(r.get("alerted_at"), "isoformat"):
                r["alerted_at"] = r["alerted_at"].isoformat()
        return jsonify(rows)
    finally:
        release_conn(conn)


# ── Config endpoint ───────────────────────────────────────────────────────────

@app.route("/api/config")
def api_config():
    cfg = load_config()
    return jsonify({
        "refresh_interval": cfg_int("monitor","refresh_interval",30),
    })

# ── API Keys ──────────────────────────────────────────────────────────────────

def _get_user_id(username: str) -> int | None:
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM auth_users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        return row[0] if row else None
    finally:
        release_conn(conn)


@app.route("/api/integrations/keys", methods=["GET"])
def api_keys_list():
    username = current_username()
    if not username:
        return {"error": "No autenticado"}, 401
    uid = _get_user_id(username)
    conn = get_monitor_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if is_admin():
            cur.execute("""
                SELECT ak.id, ak.name, ak.active, ak.created_at, ak.last_used,
                       au.username as owner
                FROM api_keys ak JOIN auth_users au ON ak.user_id = au.id
                ORDER BY ak.id DESC
            """)
        else:
            cur.execute("""
                SELECT id, name, active, created_at, last_used,
                       %s as owner
                FROM api_keys WHERE user_id = %s ORDER BY id DESC
            """, (username, uid))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        for r in rows:
            for k in ("created_at", "last_used"):
                if hasattr(r.get(k), "isoformat"):
                    r[k] = r[k].isoformat()
        return jsonify(rows)
    finally:
        release_conn(conn)


@app.route("/api/integrations/keys", methods=["POST"])
def api_keys_create():
    username = current_username()
    if not username:
        return {"error": "No autenticado"}, 401
    uid = _get_user_id(username)
    if not uid:
        return {"error": "Usuario no encontrado"}, 404
    d = request.get_json(silent=True) or {}
    name = str(d.get("name", "Mi API Key")).strip() or "Mi API Key"
    raw_key, key_hash = generate_api_key()
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO api_keys (user_id, name, key_hash)
            VALUES (%s, %s, %s) RETURNING id
        """, (uid, name, key_hash))
        new_id = cur.fetchone()[0]
        conn.commit(); cur.close()
        return jsonify({"id": new_id, "name": name, "key": raw_key,
                        "message": "Guarda esta clave, no se mostrará de nuevo."}), 201
    finally:
        release_conn(conn)


@app.route("/api/integrations/keys/<int:key_id>", methods=["DELETE"])
def api_keys_delete(key_id):
    username = current_username()
    if not username:
        return {"error": "No autenticado"}, 401
    uid = _get_user_id(username)
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        if is_admin():
            cur.execute("DELETE FROM api_keys WHERE id = %s", (key_id,))
        else:
            cur.execute("DELETE FROM api_keys WHERE id = %s AND user_id = %s", (key_id, uid))
        if cur.rowcount == 0:
            return {"error": "No encontrado o sin permisos"}, 404
        conn.commit(); cur.close()
        return {"message": "API key revocada."}
    finally:
        release_conn(conn)


@app.route("/api/integrations/keys/<int:key_id>/toggle", methods=["POST"])
def api_keys_toggle(key_id):
    username = current_username()
    if not username:
        return {"error": "No autenticado"}, 401
    uid = _get_user_id(username)
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        if is_admin():
            cur.execute("UPDATE api_keys SET active = NOT active WHERE id = %s RETURNING active", (key_id,))
        else:
            cur.execute("UPDATE api_keys SET active = NOT active WHERE id = %s AND user_id = %s RETURNING active", (key_id, uid))
        row = cur.fetchone()
        if not row:
            return {"error": "No encontrado o sin permisos"}, 404
        conn.commit(); cur.close()
        return {"active": row[0]}
    finally:
        release_conn(conn)


# ── Skill Files ───────────────────────────────────────────────────────────────

@app.route("/api/integrations/skills", methods=["GET"])
def api_skills_list():
    username = current_username()
    if not username:
        return {"error": "No autenticado"}, 401
    uid = _get_user_id(username)
    conn = get_monitor_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if session.get("role") == "admin":
            cur.execute("""
                SELECT sf.id, sf.name, sf.description, sf.active, sf.created_at,
                       LEFT(sf.content, 200) as preview, au.username as author
                FROM skill_files sf
                JOIN auth_users au ON sf.user_id = au.id
                ORDER BY sf.id DESC
            """)
        else:
            cur.execute("""
                SELECT sf.id, sf.name, sf.description, sf.active, sf.created_at,
                       LEFT(sf.content, 200) as preview, au.username as author
                FROM skill_files sf
                JOIN auth_users au ON sf.user_id = au.id
                WHERE sf.user_id = %s OR au.role = 'admin'
                ORDER BY sf.id DESC
            """, (uid,))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        for r in rows:
            if hasattr(r.get("created_at"), "isoformat"):
                r["created_at"] = r["created_at"].isoformat()
        return jsonify(rows)
    finally:
        release_conn(conn)


@app.route("/api/integrations/skills/<int:skill_id>", methods=["GET"])
def api_skills_detail(skill_id):
    username = current_username()
    if not username:
        return {"error": "No autenticado"}, 401
    uid = _get_user_id(username)
    conn = get_monitor_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Check if owner or admin
        if session.get("role") == "admin":
            cur.execute("SELECT id, name, description, content, active FROM skill_files WHERE id = %s", (skill_id,))
        else:
            cur.execute("SELECT id, name, description, content, active FROM skill_files WHERE id = %s AND user_id = %s", (skill_id, uid))
        row = cur.fetchone()
        cur.close()
        if not row:
            return {"error": "Skill no encontrada o sin permisos"}, 404
        return jsonify(dict(row))
    finally:
        release_conn(conn)


@app.route("/api/integrations/skills", methods=["POST"])
def api_skills_create():
    username = current_username()
    if not username:
        return {"error": "No autenticado"}, 401
    uid = _get_user_id(username)
    if not uid:
        return {"error": "Usuario no encontrado"}, 404
    d = request.get_json(silent=True) or {}
    name = str(d.get("name", "")).strip()
    description = str(d.get("description", "")).strip()
    content = str(d.get("content", "")).strip()
    if not name or not content:
        return {"error": "name y content son requeridos"}, 400
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO skill_files (user_id, name, description, content)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (uid, name, description, content))
        new_id = cur.fetchone()[0]
        conn.commit(); cur.close()
        return jsonify({"id": new_id, "name": name}), 201
    finally:
        release_conn(conn)


@app.route("/api/integrations/skills/<int:skill_id>", methods=["DELETE"])
def api_skills_delete(skill_id):
    username = current_username()
    if not username:
        return {"error": "No autenticado"}, 401
    uid = _get_user_id(username)
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        if session.get("role") == "admin":
            cur.execute("DELETE FROM skill_files WHERE id = %s", (skill_id,))
        else:
            cur.execute("DELETE FROM skill_files WHERE id = %s AND user_id = %s", (skill_id, uid))
        if cur.rowcount == 0:
            cur.close()
            return {"error": "No encontrado o sin permisos"}, 404
        conn.commit(); cur.close()
        return {"message": "Skill eliminada."}
    finally:
        release_conn(conn)


@app.route("/api/integrations/skills/<int:skill_id>", methods=["PUT"])
def api_skills_update(skill_id):
    username = current_username()
    if not username:
        return {"error": "No autenticado"}, 401
    uid = _get_user_id(username)
    d = request.get_json(silent=True) or {}
    name = str(d.get("name", "")).strip()
    description = str(d.get("description", "")).strip()
    content = str(d.get("content", "")).strip()
    if not name or not content:
        return {"error": "name y content son requeridos"}, 400
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        if session.get("role") == "admin":
            cur.execute("""
                UPDATE skill_files SET name = %s, description = %s, content = %s 
                WHERE id = %s
            """, (name, description, content, skill_id))
        else:
            cur.execute("""
                UPDATE skill_files SET name = %s, description = %s, content = %s 
                WHERE id = %s AND user_id = %s
            """, (name, description, content, skill_id, uid))
        if cur.rowcount == 0:
            cur.close()
            return {"error": "No encontrado o sin permisos"}, 404
        conn.commit(); cur.close()
        return {"message": "Skill actualizada."}
    finally:
        release_conn(conn)


@app.route("/api/integrations/skills/<int:skill_id>/toggle", methods=["POST"])
def api_skills_toggle(skill_id):
    username = current_username()
    if not username:
        return {"error": "No autenticado"}, 401
    uid = _get_user_id(username)
    conn = get_monitor_conn()
    try:
        cur = conn.cursor()
        if session.get("role") == "admin":
            cur.execute(
                "UPDATE skill_files SET active = NOT active WHERE id = %s RETURNING active",
                (skill_id,)
            )
        else:
            cur.execute(
                "UPDATE skill_files SET active = NOT active WHERE id = %s AND user_id = %s RETURNING active",
                (skill_id, uid)
            )
        row = cur.fetchone()
        if not row:
            cur.close()
            return {"error": "No encontrado o sin permisos"}, 404
        conn.commit(); cur.close()
        return {"active": row[0]}
    finally:
        release_conn(conn)


# ── AI Provider helpers ────────────────────────────────────────────────────────

def _load_ai_config() -> dict:
    """Read [ai] section from config.ini. Env vars take priority."""
    cfg = load_config()
    section = dict(cfg.items("ai")) if cfg.has_section("ai") else {}
    return {
        "provider":    os.environ.get("AI_PROVIDER",    section.get("provider", "none")).lower(),
        "gemini_key":  os.environ.get("GEMINI_API_KEY", section.get("gemini_api_key", "")),
        "openai_key":  os.environ.get("OPENAI_API_KEY", section.get("openai_api_key", "")),
        "model":       os.environ.get("AI_MODEL",       section.get("model", "")),
    }


def _call_gemini(prompt: str, ai_cfg: dict) -> str | None:
    """Call Google Gemini via REST. Returns text or None on failure."""
    key = ai_cfg.get("gemini_key", "")
    if not key:
        return None
    model = ai_cfg.get("model") or "gemini-2.0-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    try:
        import urllib.request, json as _json
        body = _json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 512, "temperature": 0.4},
        }).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = _json.loads(resp.read())
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        log.warning(f"Gemini error: {e}")
        return None


def _call_openai(prompt: str, ai_cfg: dict) -> str | None:
    """Call OpenAI Chat Completions via REST. Returns text or None on failure."""
    key = ai_cfg.get("openai_key", "")
    if not key:
        return None
    model = ai_cfg.get("model") or "gpt-4o-mini"
    url = "https://api.openai.com/v1/chat/completions"
    try:
        import urllib.request, json as _json
        body = _json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0.4,
        }).encode()
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        }, method="POST")
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = _json.loads(resp.read())
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.warning(f"OpenAI error: {e}")
        return None


def _build_ai_prompt(message: str, username: str, skills_ctx: str, metrics_snapshot: dict) -> str:
    """Build the full prompt to send to any AI provider."""
    metrics_summary = []
    for ds_id, entry in metrics_snapshot.items():
        m = entry.get("metrics") or {}
        if m:
            metrics_summary.append(
                f"  - DS {ds_id}: CPU={m.get('cpu_pct','?')}% | RAM={m.get('mem_pct','?')}% | "
                f"Disco={m.get('disk_used_pct','?')}% | Cache={m.get('cache_hit_ratio','?')}% | "
                f"Conexiones={m.get('threads_connected','?')}/{m.get('max_connections','?')} | "
                f"Estado={m.get('status','?')}"
            )
        else:
            metrics_summary.append(f"  - DS {ds_id}: sin datos ({entry.get('error','desconocido')})")

    metrics_text = "\n".join(metrics_summary) if metrics_summary else "  Sin datos disponibles aún."

    system_ctx = f"""Eres el asistente inteligente del sistema **DB Health Monitor**.
Tu función es responder preguntas sobre el estado de las bases de datos del usuario "{username}".
Responde en español, de forma concisa y técnica. Usa markdown (negritas, listas) cuando sea útil.
No inventes datos — usa SOLO los datos reales proporcionados abajo.

## Métricas en tiempo real (snapshot actual):
{metrics_text}

## Reglas y contexto del sistema (Skills activas):
{skills_ctx if skills_ctx else "No hay Skills activas configuradas."}

## Instrucción
Responde la siguiente consulta del usuario usando los datos reales de arriba:
{message}"""
    return system_ctx


def _call_ai(message: str, username: str, skills_ctx: str, metrics_snapshot: dict) -> str | None:
    """Try AI providers in order. Returns response text or None if unavailable."""
    ai_cfg = _load_ai_config()
    provider = ai_cfg.get("provider", "none")
    if provider == "none" and not ai_cfg.get("gemini_key") and not ai_cfg.get("openai_key"):
        return None  # No AI configured

    prompt = _build_ai_prompt(message, username, skills_ctx, metrics_snapshot)

    # Try Gemini first (if key present or provider=gemini)
    if ai_cfg.get("gemini_key") and provider in ("gemini", "none", "auto"):
        result = _call_gemini(prompt, ai_cfg)
        if result:
            return result

    # Try OpenAI as fallback
    if ai_cfg.get("openai_key") and provider in ("openai", "none", "auto"):
        result = _call_openai(prompt, ai_cfg)
        if result:
            return result

    return None


# ── Chatbox ────────────────────────────────────────────────────────────────────

def _detect_intent(text: str) -> str:
    t = text.lower()
    for keywords, intent in CHATBOX_INTENTS:
        if any(kw in t for kw in keywords):
            return intent
    return "unknown"


def _build_chatbox_response(intent: str, username: str, skills_ctx: str) -> str:
    with _cache_lock:
        snap = dict(_cache)
    owned_ids = get_owned_datasource_ids()
    snap = {k: v for k, v in snap.items() if k in owned_ids}

    def avg_metric(key):
        vals = [v["metrics"][key] for v in snap.values() if v.get("metrics") and key in v["metrics"]]
        return round(sum(vals) / len(vals), 1) if vals else None

    def fmt(v, unit="%"):
        return f"{v}{unit}" if v is not None else "sin datos aún"

    import random
    g = random.choice(["¡Hola!", "¡Buenas!", "👋 ¡Hola!"])

    if intent == "greet":
        return f"{g} Soy el asistente del **DB Health Monitor**. Puedo darte información sobre el estado de tus bases de datos. Prueba preguntando por CPU, memoria, conexiones, alertas o estado general."
    elif intent == "help":
        return ("Puedo responder preguntas sobre:\n"
                "- 🔌 **Conexiones** activas y uso\n"
                "- ⚡ **CPU** y **Memoria** del host\n"
                "- 🧱 **Disco** y almacenamiento\n"
                "- 🗃️ **Cache Hit Ratio**\n"
                "- 🔔 **Alertas** recientes\n"
                "- 🗄️ **Estado general** de las bases de datos")
    elif intent == "cpu":
        cpu = avg_metric("cpu_pct")
        level = "alto ⚠️" if (cpu or 0) > 80 else "normal ✅" if cpu is not None else ""
        return f"**CPU promedio**: {fmt(cpu)} — {level}. {'Considera revisar procesos pesados.' if (cpu or 0) > 80 else 'El servidor está respondiendo bien.'}"
    elif intent == "memory":
        mem = avg_metric("mem_pct")
        level = "alta ⚠️" if (mem or 0) > 85 else "normal ✅" if mem is not None else ""
        return f"**Memoria RAM promedio**: {fmt(mem)} — {level}."
    elif intent == "disk":
        disk = avg_metric("disk_used_pct")
        return f"**Disco usado promedio**: {fmt(disk)}. {'⚠️ Espacio bajo.' if (disk or 0) > 85 else '✅ Espacio suficiente.'}"
    elif intent == "connections":
        conn_pct = avg_metric("connection_pct")
        threads = avg_metric("threads_connected")
        return f"**Conexiones activas**: ~{int(threads or 0)} conexiones, al **{fmt(conn_pct)}** del límite máximo."
    elif intent == "cache":
        cache = avg_metric("cache_hit_ratio")
        level = "excelente ✅" if (cache or 0) >= 90 else "aceptable 🔶" if (cache or 0) >= 70 else "bajo ⚠️"
        return f"**Cache Hit Ratio promedio**: {fmt(cache)} — {level}. {'Considera aumentar la shared_buffers.' if (cache or 0) < 85 else 'El motor de BD está usando el caché eficientemente.'}"
    elif intent == "alerts":
        conn2 = get_monitor_conn()
        try:
            cur = conn2.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if owned_ids:
                cur.execute("SELECT severity, metric_name, metric_value FROM alert_log WHERE datasource_id = ANY(%s) ORDER BY id DESC LIMIT 5", (list(owned_ids),))
                alerts = [dict(r) for r in cur.fetchall()]
            else:
                alerts = []
            cur.close()
        finally:
            release_conn(conn2)
        if not alerts:
            return "✅ No hay alertas recientes registradas en tus bases de datos."
        lines = [f"🔔 **{a['severity']}** — {a['metric_name']} = {a['metric_value']}" for a in alerts]
        return "Alertas recientes:\n" + "\n".join(lines)
    elif intent == "status":
        total = len(snap)
        ok = sum(1 for v in snap.values() if (v.get("metrics") or {}).get("status") == "OK")
        warn = sum(1 for v in snap.values() if (v.get("metrics") or {}).get("status") == "WARNING")
        crit = sum(1 for v in snap.values() if (v.get("metrics") or {}).get("status") == "CRITICAL")
        return (f"📊 **Estado general** de tus {total} fuentes de datos:\n"
                f"- ✅ OK: {ok}\n"
                f"- 🔶 WARNING: {warn}\n"
                f"- 🔴 CRITICAL: {crit}")
    elif intent == "datasources":
        total = len(snap)
        names = []
        conn2 = get_monitor_conn()
        try:
            cur = conn2.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT nombre, tipo_db FROM datasources WHERE id = ANY(%s)", (list(owned_ids) if owned_ids else [-1],))
            names = [f"{r['nombre']} ({r['tipo_db']})" for r in cur.fetchall()]
            cur.close()
        finally:
            release_conn(conn2)
        return f"Tienes **{total}** fuentes de datos registradas:\n" + "\n".join(f"- {n}" for n in names)
    elif intent == "uptime":
        uptime = avg_metric("uptime_seconds")
        if uptime is None:
            return "No tengo datos de uptime disponibles aún."
        days = int(uptime // 86400)
        hours = int((uptime % 86400) // 3600)
        return f"⏱️ **Uptime promedio** de tus bases de datos: **{days}d {hours}h**."
    else:
        skill_hint = f"\n\n*(Contexto de skill activa disponible)*" if skills_ctx else ""
        return (f"Hmm, no estoy seguro de entender esa consulta. Intenta preguntarme sobre:\n"
                "cpu, memoria, disco, conexiones, cache, alertas, estado o uptime." + skill_hint)


@app.route("/api/integrations/chat", methods=["POST"])
def api_chat():
    # Accepts both session auth AND Bearer token (external systems)
    bearer = resolve_bearer_user()
    if bearer:
        session["username"] = bearer["username"]
        session["role"] = bearer["role"]

    username = current_username()
    if not username:
        return {"error": "No autenticado. Usa sesión o Bearer token."}, 401
    uid = _get_user_id(username)
    d = request.get_json(silent=True) or {}
    message = str(d.get("message", "")).strip()
    if not message:
        return {"error": "message requerido"}, 400

    # Load active skills as context
    skills_ctx = ""
    active_skills_names = []
    if uid:
        conn2 = get_monitor_conn()
        try:
            cur = conn2.cursor()
            # Viewers see active admin skills + active own skills
            if session.get("role") == "admin":
                cur.execute("""
                    SELECT sf.name, sf.content 
                    FROM skill_files sf
                    WHERE sf.active = TRUE ORDER BY sf.id
                """)
            else:
                cur.execute("""
                    SELECT sf.name, sf.content 
                    FROM skill_files sf
                    JOIN auth_users au ON sf.user_id = au.id
                    WHERE (sf.user_id = %s OR au.role = 'admin') AND sf.active = TRUE
                    ORDER BY sf.id
                """, (uid,))
            rows = cur.fetchall()
            cur.close()
            if rows:
                skills_ctx = "\n\n---\n\n".join(f"# Skill: {r[0]}\n{r[1]}" for r in rows)
                active_skills_names = [r[0] for r in rows]
        finally:
            release_conn(conn2)

    # Get current metrics snapshot for the user
    with _cache_lock:
        metrics_snap = dict(_cache)
    owned_ids = get_owned_datasource_ids()
    metrics_snap = {k: v for k, v in metrics_snap.items() if k in owned_ids}

    # Try AI first (Gemini / OpenAI) — uses skills_ctx as system prompt
    ai_reply = _call_ai(message, username, skills_ctx, metrics_snap)
    if ai_reply:
        return jsonify({"reply": ai_reply, "intent": "ai", "ai": True, "active_skills": active_skills_names})

    # Fallback: keyword-based matcher
    intent = _detect_intent(message)
    reply = _build_chatbox_response(intent, username, skills_ctx)
    return jsonify({"reply": reply, "intent": intent, "ai": False, "active_skills": active_skills_names})


# ── API v1 aliases (públicos con Bearer token) ────────────────────────────────

@app.route("/api/v1/health")
def api_v1_health():
    return api_health()

@app.route("/api/v1/metrics")
def api_v1_metrics():
    return api_metrics()

@app.route("/api/v1/datasources", methods=["GET"])
def api_v1_datasources():
    return api_ds_list()

@app.route("/api/v1/summary")
def api_v1_summary():
    return api_summary_global()

@app.route("/api/v1/alerts")
def api_v1_alerts():
    return api_alerts_history()

@app.route("/api/v1/history")
def api_v1_history():
    return api_history()

@app.route("/api/v1/files")
def api_v1_files():
    return api_files()

@app.route("/api/v1/files/read")
def api_v1_files_read():
    return api_files_read()

@app.route("/api/skill/download")
def download_skill():
    """Serve the SKILL.md file as a direct download."""
    import os as _os
    skill_path = _os.path.join(
        _os.path.dirname(__file__),
        ".agents", "skills", "db-health-monitor", "SKILL.md"
    )
    if not _os.path.isfile(skill_path):
        return jsonify({"error": "SKILL.md not found"}), 404
    from flask import send_file
    return send_file(
        skill_path,
        as_attachment=True,
        download_name="db-health-monitor-skill.md",
        mimetype="text/markdown"
    )

# ── Arranque ──────────────────────────────────────────────────────────────────

def startup():
    log.info("=== DB Health Monitor arrancando ===")
    if _PSUTIL:
        try: psutil.cpu_percent(interval=None)
        except: pass
    t = threading.Thread(target=background_collector, daemon=True)
    t.start()

if __name__ == "__main__":
    startup()
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
else:
    startup()

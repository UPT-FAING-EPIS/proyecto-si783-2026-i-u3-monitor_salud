#!/usr/bin/env python3
"""
helper.py — Puente CLI entre la extensión de VS Code y el Monitor de Salud.
Reutiliza la lógica de db_connection.py local y encapsula la lógica de server.py de forma autocontenida.
"""

import sys
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

# Add vscode/ folder to sys.path to load local db_connection
sys.path.insert(0, str(Path(__file__).parent.resolve()))

try:
    import db_connection
except ImportError as e:
    print(json.dumps({"error": f"No se pudo importar db_connection local: {e}"}))
    sys.exit(1)

# Initialize psutil
try:
    import psutil
    _proc = psutil.Process()
    _PSUTIL = True
except Exception:
    psutil = None; _proc = None; _PSUTIL = False

# BASE_DIR represents the workspace project root (parent of vscode/)
BASE_DIR = Path(__file__).parent.parent.resolve()

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


# ── Métricas y Recolección de Archivos (Clonados de server.py) ──────────────────

def _default_file_roots(ds: dict) -> dict:
    tipo = (ds.get("tipo_db") or "postgresql").lower()
    cfg = db_connection.load_config()
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


def collect_pg_metrics(ds: dict) -> dict:
    conn = db_connection.connect_to_datasource(ds, timeout=8)
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
    conn = db_connection.connect_to_datasource(ds, timeout=8)
    cur  = conn.cursor()

    cur.execute("SHOW GLOBAL STATUS")
    status_vars = {row[0]: row[1] for row in cur.fetchall()}

    cur.execute("SHOW GLOBAL VARIABLES LIKE 'max_connections'")
    max_conn = int((cur.fetchone() or [None, 100])[1])

    threads_connected = int(status_vars.get("Threads_connected", 0))
    threads_running   = int(status_vars.get("Threads_running",   0))
    slow_queries      = int(status_vars.get("Slow_queries",       0))
    uptime_seconds    = int(status_vars.get("Uptime", 0))

    cur.execute("""
        SELECT COUNT(*) FROM information_schema.processlist
        WHERE command != 'Sleep'
    """)
    threads_waiting = int((cur.fetchone() or [0])[0])

    pool_reads    = int(status_vars.get("Innodb_buffer_pool_reads",         0))
    pool_requests = int(status_vars.get("Innodb_buffer_pool_read_requests", 1))
    if pool_requests > 0:
        cache_hit = round((1 - pool_reads / pool_requests) * 100, 2)
    else:
        cache_hit = 99.9
    cache_hit = max(0.0, min(100.0, cache_hit))

    cur.execute("""
        SELECT COALESCE(SUM(data_length + index_length), 0) / 1024 / 1024
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
    """)
    db_mb = round(float((cur.fetchone() or [0])[0]), 2)

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
    m = collect_mysql_metrics(ds)
    m["tipo_db"] = "mariadb"
    return m


def collect_sqlserver_metrics(ds: dict) -> dict:
    conn = db_connection.connect_to_datasource(ds, timeout=8)
    cur  = conn.cursor()

    cur.execute("SELECT value_in_use FROM sys.configurations WHERE name = 'max connections'")
    max_conn_val = int((cur.fetchone() or [0])[0])
    max_conn = max_conn_val if max_conn_val > 0 else 32767

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

    cur.execute("""
        SELECT CAST(SUM(size) * 8.0 / 1024 AS FLOAT)
        FROM sys.master_files
        WHERE database_id = DB_ID()
    """)
    db_mb = round(float((cur.fetchone() or [0])[0] or 0), 2)

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

        wt          = srv.get("wiredTiger", {}).get("cache", {})
        reads_into  = int(wt.get("pages read into cache",        1))
        reads_req   = int(wt.get("pages requested from the cache", 1))
        cache_hit   = round((1 - reads_into / max(reads_req, 1)) * 100, 2)
        cache_hit   = max(0.0, min(100.0, cache_hit))

        db_stats    = client[ds["database"]].command("dbStats")
        db_mb       = round(db_stats.get("dataSize", 0) / 1024 / 1024, 2)

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


# ── Lógica CLI de Consultas ───────────────────────────────────────────────────

def get_datasources():
    conn = db_connection.get_monitor_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, tipo_db, host, puerto, usuario, database, activa, owner_username
            FROM datasources
            ORDER BY id
        """)
        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        cur.execute("""
            SELECT datasource_id, status 
            FROM health_snapshots 
            WHERE id IN (
                SELECT MAX(id) FROM health_snapshots GROUP BY datasource_id
            )
        """)
        status_map = {row[0]: row[1] for row in cur.fetchall()}
        cur.close()
        
        for r in rows:
            r["activa"] = bool(r["activa"])
            if not r["activa"]:
                r["status"] = "disabled"
            else:
                r["status"] = status_map.get(r["id"], "unknown")
                
        return rows
    finally:
        db_connection.release_conn(conn)


def get_live_metrics(ds_id):
    conn = db_connection.get_monitor_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, tipo_db, host, puerto, usuario, password, database, activa
            FROM datasources WHERE id = %s
        """, (ds_id,))
        columns = [desc[0] for desc in cur.description]
        row = cur.fetchone()
        cur.close()
        
        if not row:
            return {"error": f"Datasource {ds_id} no encontrado"}
            
        ds = dict(zip(columns, row))
        ds["activa"] = bool(ds["activa"])
        
        if not ds["activa"]:
            return {"error": "El datasource está inactivo"}

        tipo = (ds.get("tipo_db") or "postgresql").lower()
        if tipo == "postgresql":
            metrics = collect_pg_metrics(ds)
        elif tipo == "mysql":
            metrics = collect_mysql_metrics(ds)
        elif tipo == "mariadb":
            metrics = collect_mariadb_metrics(ds)
        elif tipo in ("sqlserver", "mssql"):
            metrics = collect_sqlserver_metrics(ds)
        elif tipo == "mongodb":
            metrics = collect_mongodb_metrics(ds)
        else:
            return {"error": f"Tipo '{tipo}' no soportado"}
            
        return {"metrics": metrics}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db_connection.release_conn(conn)


def get_files(ds_id):
    conn = db_connection.get_monitor_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, tipo_db, host, puerto, usuario, database, activa
            FROM datasources WHERE id = %s
        """, (ds_id,))
        columns = [desc[0] for desc in cur.description]
        row = cur.fetchone()
        cur.close()
        
        if not row:
            return {"error": "Datasource no encontrado"}
            
        ds = dict(zip(columns, row))
        files = build_file_inventory(ds)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db_connection.release_conn(conn)


def read_file(ds_id, file_path):
    conn = db_connection.get_monitor_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, tipo_db, host, puerto, usuario, database, activa
            FROM datasources WHERE id = %s
        """, (ds_id,))
        columns = [desc[0] for desc in cur.description]
        row = cur.fetchone()
        cur.close()
        
        if not row:
            return {"error": "Datasource no encontrado"}
            
        ds = dict(zip(columns, row))
        files = build_file_inventory(ds)
        allowed_paths = {f["path"] for f in files}
        
        if file_path not in allowed_paths:
            return {"error": "Acceso denegado a este archivo (fuera del inventario)"}
            
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return {"error": "Archivo no encontrado"}
            
        st = p.stat()
        if st.st_size > 2 * 1024 * 1024:
            return {"error": "El archivo supera el límite de 2 MB"}
            
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            
        return {
            "path": file_path,
            "filename": p.name,
            "size_bytes": st.st_size,
            "content": content
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db_connection.release_conn(conn)


def get_history(ds_id):
    conn = db_connection.get_monitor_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, datasource_id, captured_at, max_connections, threads_connected, 
                   threads_running, connection_pct, qps, slow_queries, cache_hit_ratio, 
                   db_size_mb, cpu_pct, mem_pct, status
            FROM health_snapshots 
            WHERE datasource_id = %s
            ORDER BY id DESC LIMIT 50
        """, (ds_id,))
        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        
        for r in rows:
            if r.get("captured_at"):
                r["captured_at"] = r["captured_at"].isoformat()
                
        return list(reversed(rows))
    except Exception as e:
        return {"error": str(e)}
    finally:
        db_connection.release_conn(conn)


def get_alerts(ds_id):
    conn = db_connection.get_monitor_conn()
    try:
        cur = conn.cursor()
        if ds_id is not None:
            cur.execute("""
                SELECT id, datasource_id, alerted_at, severity, metric_name, metric_value, threshold, message
                FROM alert_log 
                WHERE datasource_id = %s
                ORDER BY id DESC LIMIT 20
            """, (ds_id,))
        else:
            cur.execute("""
                SELECT id, datasource_id, alerted_at, severity, metric_name, metric_value, threshold, message
                FROM alert_log 
                ORDER BY id DESC LIMIT 100
            """)
        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        
        for r in rows:
            if r.get("alerted_at"):
                r["alerted_at"] = r["alerted_at"].isoformat()
                
        return rows
    except Exception as e:
        return {"error": str(e)}
    finally:
        db_connection.release_conn(conn)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Falta especificar el comando (get_datasources, get_metrics, etc.)"}))
        sys.exit(1)
        
    cmd = sys.argv[1]
    
    if cmd == "get_datasources":
        res = get_datasources()
    elif cmd == "get_metrics":
        if len(sys.argv) < 3:
            res = {"error": "Falta el ID del datasource"}
        else:
            res = get_live_metrics(int(sys.argv[2]))
    elif cmd == "get_files":
        if len(sys.argv) < 3:
            res = {"error": "Falta el ID del datasource"}
        else:
            res = get_files(int(sys.argv[2]))
    elif cmd == "read_file":
        if len(sys.argv) < 4:
            res = {"error": "Falta el ID del datasource y/o la ruta del archivo"}
        else:
            res = read_file(int(sys.argv[2]), sys.argv[3])
    elif cmd == "get_history":
        if len(sys.argv) < 3:
            res = {"error": "Falta el ID del datasource"}
        else:
            res = get_history(int(sys.argv[2]))
    elif cmd == "get_alerts":
        if len(sys.argv) < 3:
            res = get_alerts(None)
        else:
            res = get_alerts(int(sys.argv[2]))
    else:
        res = {"error": f"Comando '{cmd}' desconocido"}
        
    print(json.dumps(res, ensure_ascii=False))

if __name__ == "__main__":
    main()

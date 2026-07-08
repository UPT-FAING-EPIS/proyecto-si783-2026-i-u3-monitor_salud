#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import paramiko
import pymongo
from db_connection import get_monitor_conn, release_conn
from werkzeug.security import generate_password_hash

VM_HOST = "38.250.116.71"
VM_PORT = 22
VM_USER = "root"
VM_PASS = "upt2026"

def run_ssh_command(ssh, cmd):
    print(f"SSH Executing: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    return out.strip(), err.strip()

def create_databases():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to VM {VM_HOST} via SSH...")
        ssh.connect(VM_HOST, port=VM_PORT, username=VM_USER, password=VM_PASS, timeout=15)
        print("Connected!")

        # 1. PostgreSQL DBs
        pg_dbs = ["db_ventas_prod", "db_rrhh_test"]
        for db in pg_dbs:
            out, _ = run_ssh_command(ssh, f"sudo -u postgres psql -t -Ac \"SELECT 1 FROM pg_database WHERE datname='{db}'\"")
            if out == "1":
                print(f"PostgreSQL Database '{db}' already exists. Skipping.")
            else:
                run_ssh_command(ssh, f"sudo -u postgres psql -c \"CREATE DATABASE {db};\"")
                print(f"Created PostgreSQL Database '{db}'.")
            run_ssh_command(ssh, f"sudo -u postgres psql -d {db} -c \"GRANT ALL PRIVILEGES ON DATABASE {db} TO monitor;\"")

        # 2. MongoDB DB (remote connection through pymongo directly since bind_ip_all is active)
        print("\nCreating MongoDB Database 'db_tienda_mongo'...")
        mongo_uri = f"mongodb://{VM_HOST}:27017/"
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        mongo_db = client["db_tienda_mongo"]
        # Mongo needs a collection and document insertion to actually initialize/exist the DB
        col = mongo_db["productos"]
        if col.count_documents({}) == 0:
            col.insert_one({"nombre": "Laptop Celeste Premium", "precio": 1299.99, "stock": 10})
            print("MongoDB Database 'db_tienda_mongo' initialized with a test collection and document.")
        else:
            print("MongoDB Database 'db_tienda_mongo' already initialized.")
        client.close()

    except Exception as e:
        print(f"Error creating databases: {e}")
        sys.exit(1)
    finally:
        ssh.close()

def register_datasources():
    username = "TM95Gerardo"
    password_plain = "123456"
    password_hash = generate_password_hash(password_plain)

    conn = get_monitor_conn()
    try:
        with conn.cursor() as cur:
            # 1. Ensure user TM95Gerardo exists
            cur.execute("SELECT id FROM auth_users WHERE username = %s LIMIT 1", (username,))
            row = cur.fetchone()
            if row:
                print(f"\nUser '{username}' already exists.")
            else:
                cur.execute(
                    "INSERT INTO auth_users (username, password, role, active) VALUES (%s, %s, 'viewer', TRUE)",
                    (username, password_hash)
                )
                print(f"\nCreated User '{username}'.")

            # 2. Register PostgreSQL Databases
            pg_dbs = ["db_ventas_prod", "db_rrhh_test"]
            for db in pg_dbs:
                name = f"PostgreSQL - {db.replace('_', ' ').title()}"
                cur.execute("SELECT id FROM datasources WHERE owner_username = %s AND database = %s LIMIT 1", (username, db))
                if cur.fetchone():
                    print(f"PostgreSQL Datasource '{db}' already registered.")
                else:
                    cur.execute(
                        """INSERT INTO datasources (owner_username, nombre, tipo_db, host, puerto, usuario, password, database, activa)
                           VALUES (%s, %s, 'postgresql', %s, 5432, 'monitor', 'Monitor2026!@#', %s, TRUE)""",
                        (username, name, VM_HOST, db)
                    )
                    print(f"Registered PostgreSQL Datasource '{name}'.")

            # 3. Register MongoDB Database
            mongo_db = "db_tienda_mongo"
            name = "MongoDB - Tienda Mongo"
            cur.execute("SELECT id FROM datasources WHERE owner_username = %s AND database = %s LIMIT 1", (username, mongo_db))
            if cur.fetchone():
                print("MongoDB Datasource already registered.")
            else:
                cur.execute(
                    """INSERT INTO datasources (owner_username, nombre, tipo_db, host, puerto, usuario, password, database, activa)
                       VALUES (%s, %s, 'mongodb', %s, 27017, '', '', %s, TRUE)""",
                    (username, name, VM_HOST, mongo_db)
                )
                print(f"Registered MongoDB Datasource '{name}'.")

            conn.commit()
            print("\nRegistration completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"DB Error: {e}")
    finally:
        release_conn(conn)

if __name__ == "__main__":
    create_databases()
    register_datasources()

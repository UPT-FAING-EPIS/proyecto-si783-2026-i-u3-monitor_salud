#!/usr/bin/env python3
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import paramiko
from db_connection import get_monitor_conn, release_conn
from werkzeug.security import generate_password_hash

# Config VM
VM_HOST = "38.250.116.71"
VM_PORT = 22
VM_USER = "root"
VM_PASS = "upt2026"

# Test databases to create on the VM
TEST_DBS = ["db_ventas_prod", "db_rrhh_test", "db_inventario_analytics"]

def run_ssh_command(ssh, cmd):
    print(f"SSH Executing: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if out:
        print(f"  [Out]: {out.strip()}")
    if err:
        print(f"  [Err]: {err.strip()}")
    return out, err

def create_dbs_on_vm():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to VM {VM_HOST} via SSH...")
        ssh.connect(VM_HOST, port=VM_PORT, username=VM_USER, password=VM_PASS, timeout=15)
        print("Connected!")

        for db in TEST_DBS:
            # Check if database already exists
            check_cmd = f"sudo -u postgres psql -t -Ac \"SELECT 1 FROM pg_database WHERE datname='{db}'\""
            out, _ = run_ssh_command(ssh, check_cmd)
            if out.strip() == "1":
                print(f"Database '{db}' already exists on VM. Skipping creation.")
            else:
                create_cmd = f"sudo -u postgres psql -c \"CREATE DATABASE {db};\""
                run_ssh_command(ssh, create_cmd)

            # Grant privileges to the monitor user on this database
            grant_cmd = f"sudo -u postgres psql -d {db} -c \"GRANT ALL PRIVILEGES ON DATABASE {db} TO monitor;\""
            run_ssh_command(ssh, grant_cmd)

    except Exception as e:
        print(f"SSH Error: {e}")
        sys.exit(1)
    finally:
        ssh.close()

def register_dbs_in_system():
    # Credentials to monitor
    username = "TM95Gerardo"
    password_plain = "123456"
    password_hash = generate_password_hash(password_plain)

    conn = get_monitor_conn()
    try:
        with conn.cursor() as cur:
            # 1. Create or get user 'TM95Gerardo'
            cur.execute("SELECT id FROM auth_users WHERE username = %s LIMIT 1", (username,))
            row = cur.fetchone()
            if row:
                user_id = row[0]
                print(f"User '{username}' already exists with ID: {user_id}")
            else:
                cur.execute(
                    "INSERT INTO auth_users (username, password, role, active) VALUES (%s, %s, 'viewer', TRUE) RETURNING id",
                    (username, password_hash)
                )
                user_id = cur.fetchone()[0]
                print(f"User '{username}' created successfully with ID: {user_id}")

            # 2. Register each database in the datasources table
            for db in TEST_DBS:
                db_name = f"PostgreSQL - {db.replace('_', ' ').title()}"
                
                # Check if this datasource is already registered for this user
                cur.execute(
                    "SELECT id FROM datasources WHERE owner_username = %s AND database = %s LIMIT 1",
                    (username, db)
                )
                exists = cur.fetchone()
                if exists:
                    print(f"Datasource '{db_name}' ({db}) is already registered for {username}.")
                else:
                    cur.execute(
                        """INSERT INTO datasources (owner_username, nombre, tipo_db, host, puerto, usuario, password, database, activa)
                           VALUES (%s, %s, 'postgresql', %s, 5432, 'monitor', 'Monitor2026!@#', %s, TRUE)""",
                        (username, db_name, VM_HOST, db)
                    )
                    print(f"Registered datasource '{db_name}' ({db}) for user {username}.")
            
            conn.commit()
            print("\nRegistration completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"DB Error: {e}")
    finally:
        release_conn(conn)

if __name__ == "__main__":
    print("=== Step 1: Creating databases on VM ===")
    create_dbs_on_vm()
    print("\n=== Step 2: Registering databases in System ===")
    register_dbs_in_system()

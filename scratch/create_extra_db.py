#!/usr/bin/env python3
import paramiko

VM_HOST = "38.250.116.71"
VM_PORT = 22
VM_USER = "root"
VM_PASS = "upt2026"

DB_NAME = "db_logistica_prod"

def create_db():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to VM {VM_HOST} via SSH...")
        ssh.connect(VM_HOST, port=VM_PORT, username=VM_USER, password=VM_PASS, timeout=15)
        print("Connected!")

        # Check if database already exists
        stdin, stdout, stderr = ssh.exec_command(f"sudo -u postgres psql -t -Ac \"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'\"")
        exists = stdout.read().decode().strip()
        
        if exists == "1":
            print(f"Database '{DB_NAME}' already exists on VM.")
        else:
            print(f"Creating database '{DB_NAME}'...")
            ssh.exec_command(f"sudo -u postgres psql -c \"CREATE DATABASE {DB_NAME};\"")
            # small pause
            import time
            time.sleep(1)
            print(f"Database '{DB_NAME}' created.")

        print(f"Granting privileges on '{DB_NAME}' to monitor user...")
        ssh.exec_command(f"sudo -u postgres psql -d {DB_NAME} -c \"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO monitor;\"")
        print("Privileges granted successfully!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    create_db()

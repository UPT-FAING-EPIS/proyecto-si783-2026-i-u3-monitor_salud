#!/usr/bin/env python3
import paramiko

VM_HOST = "38.250.116.71"
VM_PORT = 22
VM_USER = "root"
VM_PASS = "upt2026"

def check_vm_services():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VM_HOST, port=VM_PORT, username=VM_USER, password=VM_PASS, timeout=15)
        print("Checking active database engines on the VM:")
        
        # Check pg
        _, stdout, _ = ssh.exec_command("pgrep -fa postgres")
        print(f"Postgres status:\n{stdout.read().decode().strip()}")
        
        # Check mysql/mariadb
        _, stdout, _ = ssh.exec_command("pgrep -fa mysql || pgrep -fa mariadb")
        print(f"MySQL/MariaDB status:\n{stdout.read().decode().strip()}")
        
        # Check mongodb
        _, stdout, _ = ssh.exec_command("pgrep -fa mongo")
        print(f"MongoDB status:\n{stdout.read().decode().strip()}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    check_vm_services()

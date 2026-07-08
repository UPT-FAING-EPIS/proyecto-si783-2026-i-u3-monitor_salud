#!/usr/bin/env python3
import paramiko

VM_HOST = "38.250.116.71"
VM_PORT = 22
VM_USER = "root"
VM_PASS = "upt2026"

def inspect_vm_webserver():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VM_HOST, port=VM_PORT, username=VM_USER, password=VM_PASS, timeout=15)
        print("=== Checking VM Web Services ===")
        
        # 1. Listening ports
        _, stdout, _ = ssh.exec_command("ss -tlnp | grep -E '5000|80|443|8080'")
        print(f"Listening Ports:\n{stdout.read().decode().strip()}\n")
        
        # 2. Running processes
        _, stdout, _ = ssh.exec_command("ps aux | grep -E 'python|gunicorn' | grep -v grep")
        print(f"Python/Gunicorn Processes:\n{stdout.read().decode().strip()}\n")
        
        # 3. Systemd services
        _, stdout, _ = ssh.exec_command("systemctl list-units --type=service | grep -E 'monitor|gunicorn|health|db'")
        print(f"Systemd services status:\n{stdout.read().decode().strip()}\n")
        
    except Exception as e:
        print(f"Error inspecting VM: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    inspect_vm_webserver()

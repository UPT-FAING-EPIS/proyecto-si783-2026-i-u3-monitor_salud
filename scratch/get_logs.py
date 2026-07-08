#!/usr/bin/env python3
import paramiko

VM_HOST = "38.250.116.71"
VM_PORT = 22
VM_USER = "root"
VM_PASS = "upt2026"

def check_vm_logs():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VM_HOST, port=VM_PORT, username=VM_USER, password=VM_PASS, timeout=15)
        print("=== Checking dbmonitor.service logs (last 30 lines) ===")
        _, stdout, _ = ssh.exec_command("journalctl -u dbmonitor.service -n 30 --no-pager")
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        print("=== Checking VM Firewall Status ===")
        _, stdout, _ = ssh.exec_command("ufw status verbose || echo 'ufw not installed/active'")
        print(stdout.read().decode('utf-8', errors='ignore'))
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    check_vm_logs()

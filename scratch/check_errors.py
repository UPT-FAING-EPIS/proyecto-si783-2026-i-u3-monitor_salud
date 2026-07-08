#!/usr/bin/env python3
import paramiko

VM_HOST = "38.250.116.71"
VM_PORT = 22
VM_USER = "root"
VM_PASS = "upt2026"

def check_immediate_errors():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VM_HOST, port=VM_PORT, username=VM_USER, password=VM_PASS, timeout=15)
        print("=== dbmonitor status after restart ===")
        _, stdout, _ = ssh.exec_command("systemctl status dbmonitor.service --no-pager")
        out = stdout.read().decode('utf-8', errors='ignore')
        # Clean unicode characters that crash Windows CP1252
        out_clean = out.encode('ascii', 'ignore').decode('ascii')
        print(out_clean)
        
        print("=== dbmonitor journal logs (last 20 lines) ===")
        _, stdout, _ = ssh.exec_command("journalctl -u dbmonitor.service -n 20 --no-pager")
        out2 = stdout.read().decode('utf-8', errors='ignore')
        out2_clean = out2.encode('ascii', 'ignore').decode('ascii')
        print(out2_clean)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    check_immediate_errors()

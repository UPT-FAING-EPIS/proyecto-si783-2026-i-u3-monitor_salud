#!/usr/bin/env python3
import paramiko

VM_HOST = "38.250.116.71"
VM_PORT = 22
VM_USER = "root"
VM_PASS = "upt2026"

def restart_and_test_locally():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VM_HOST, port=VM_PORT, username=VM_USER, password=VM_PASS, timeout=15)
        print("=== Restarting dbmonitor.service on VM ===")
        _, stdout, stderr = ssh.exec_command("systemctl restart dbmonitor.service")
        # Read to block until complete
        stdout.read()
        err = stderr.read().decode().strip()
        if err:
            print(f"Error during restart: {err}")
        else:
            print("Service restarted successfully!")

        print("\n=== Testing connection locally from inside the VM ===")
        # Run curl internally to see if it responds 200 OK
        _, stdout, _ = ssh.exec_command("curl -I http://127.0.0.1:5000/")
        print(f"Internal curl response:\n{stdout.read().decode().strip()}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    restart_and_test_locally()

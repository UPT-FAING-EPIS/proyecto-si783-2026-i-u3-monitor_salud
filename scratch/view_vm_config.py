#!/usr/bin/env python3
import paramiko

VM_HOST = "38.250.116.71"
VM_PORT = 22
VM_USER = "root"
VM_PASS = "upt2026"

def view_vm_config():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VM_HOST, port=VM_PORT, username=VM_USER, password=VM_PASS, timeout=15)
        print("=== Reading /opt/monitor/config.ini from VM ===")
        sftp = ssh.open_sftp()
        try:
            with sftp.open("/opt/monitor/config.ini", "r") as f:
                print(f.read().decode('utf-8'))
        except Exception as ex:
            print(f"Error reading file: {ex}")
        finally:
            sftp.close()
    except Exception as e:
        print(f"Error connecting: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    view_vm_config()

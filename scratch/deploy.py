#!/usr/bin/env python3
import paramiko
import os

VM_HOST = "38.250.116.71"
VM_PORT = 22
VM_USER = "root"
VM_PASS = "upt2026"

LOCAL_DIR = r"c:\Users\Gerardo\Documents\GitHub\proyecto-si783-2026-i-u3-monitor_salud"
VM_DIR = "/opt/monitor"

FILES_TO_DEPLOY = [
    ("server.py", "server.py"),
    ("config.ini", "config.ini"),
    (os.path.join("templates", "index.html"), "templates/index.html"),
    (os.path.join("static", "style.css"), "static/style.css"),
    (os.path.join("static", "dashboard.js"), "static/dashboard.js"),
]

def deploy():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to VM {VM_HOST} via SSH...")
        ssh.connect(VM_HOST, port=VM_PORT, username=VM_USER, password=VM_PASS, timeout=15)
        print("Connected!")

        sftp = ssh.open_sftp()
        print("\n=== Uploading Files ===")
        for local_rel, vm_rel in FILES_TO_DEPLOY:
            local_path = os.path.join(LOCAL_DIR, local_rel)
            vm_path = f"{VM_DIR}/{vm_rel}"
            
            # Ensure folder exists on VM
            vm_folder = os.path.dirname(vm_path)
            try:
                sftp.stat(vm_folder)
            except IOError:
                print(f"Creating remote folder: {vm_folder}")
                ssh.exec_command(f"mkdir -p {vm_folder}")
                # small pause to let directory be created
                import time
                time.sleep(0.5)

            print(f"Uploading: {local_rel}  ->  {vm_path}")
            sftp.put(local_path, vm_path)
        
        sftp.close()
        print("\n=== Restarting dbmonitor.service ===")
        stdin, stdout, stderr = ssh.exec_command("systemctl restart dbmonitor.service")
        # Block until restart completes
        stdout.read()
        err = stderr.read().decode().strip()
        if err:
            print(f"Restart Error: {err}")
        else:
            print("dbmonitor.service restarted successfully on VM!")

    except Exception as e:
        print(f"\nDeployment failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy()

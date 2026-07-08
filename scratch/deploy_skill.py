#!/usr/bin/env python3
"""Uploads the .agents/skills directory and SKILL.md to the VM."""
import paramiko
import os

VM_HOST = "38.250.116.71"
VM_PORT = 22
VM_USER = "root"
VM_PASS = "upt2026"

LOCAL_DIR = r"c:\Users\Gerardo\Documents\GitHub\proyecto-si783-2026-i-u1-monitor_de_salud_espinoza_vargas"
VM_DIR = "/opt/monitor"

SKILL_LOCAL = os.path.join(LOCAL_DIR, ".agents", "skills", "db-health-monitor", "SKILL.md")
SKILL_VM    = f"{VM_DIR}/.agents/skills/db-health-monitor/SKILL.md"

def deploy_skill():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to VM {VM_HOST} via SSH...")
        ssh.connect(VM_HOST, port=VM_PORT, username=VM_USER, password=VM_PASS, timeout=15)
        print("Connected!")

        # Ensure remote directory exists
        vm_folder = os.path.dirname(SKILL_VM)
        ssh.exec_command(f"mkdir -p {vm_folder}")
        import time; time.sleep(0.5)

        sftp = ssh.open_sftp()
        print(f"Uploading: SKILL.md  ->  {SKILL_VM}")
        sftp.put(SKILL_LOCAL, SKILL_VM)
        sftp.close()

        print("SKILL.md uploaded successfully!")

    except Exception as e:
        print(f"\nUpload failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy_skill()

#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db_connection import get_monitor_conn, release_conn
from werkzeug.security import generate_password_hash

def check_privileges():
    conn = get_monitor_conn()
    try:
        with conn.cursor() as cur:
            # Check user role attributes
            cur.execute("SELECT rolname, rolcreatedb, rolsuper FROM pg_roles WHERE rolname = CURRENT_USER")
            row = cur.fetchone()
            print(f"Current PG user attributes: {row}")
    except Exception as e:
        print(f"Error checking attributes: {e}")
    finally:
        release_conn(conn)

if __name__ == "__main__":
    check_privileges()

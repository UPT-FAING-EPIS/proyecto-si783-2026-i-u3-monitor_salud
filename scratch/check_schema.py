#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db_connection import get_monitor_conn, release_conn

def check_table_schema():
    conn = get_monitor_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'datasources'
            """)
            rows = cur.fetchall()
            print("Table 'datasources' columns:")
            for r in rows:
                print(f"  {r[0]}: {r[1]}")
    except Exception as e:
        print(f"Error checking schema: {e}")
    finally:
        release_conn(conn)

if __name__ == "__main__":
    check_table_schema()

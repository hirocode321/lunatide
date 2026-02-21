import sqlite3
import os

db_path = 'moon_data.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    print("Tables:", tables)
    for table_name in [t[0] for t in tables]:
        print(f"\nSchema for {table_name}:")
        c.execute(f"PRAGMA table_info({table_name});")
        print(c.fetchall())
else:
    print(f"{db_path} not found.")

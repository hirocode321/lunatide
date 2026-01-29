import sqlite3

def cleanup():
    db_path = 'inquiries.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Dropping old tables from inquiries.db...")
    cursor.execute("DROP TABLE IF EXISTS moon_data")
    cursor.execute("DROP TABLE IF EXISTS astro_events")
    
    conn.commit()
    
    # Verify
    tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    print(f"Remaining tables: {tables}")
    
    conn.close()

if __name__ == "__main__":
    cleanup()

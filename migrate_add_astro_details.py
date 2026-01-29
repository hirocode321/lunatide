import sqlite3
import os

DB_PATH = 'moon_data.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check existing columns
    c.execute("PRAGMA table_info(astro_events)")
    columns = [row[1] for row in c.fetchall()]
    
    new_columns = {
        'direction': 'TEXT',
        'time_range': 'TEXT',
        'altitude': 'TEXT',
        'viewing_mode': 'TEXT', # 'naked', 'binoculars'
        'visibility_score': 'INTEGER DEFAULT 3' # 1-5
    }
    
    for col, data_type in new_columns.items():
        if col not in columns:
            print(f"Adding column {col}...")
            try:
                c.execute(f"ALTER TABLE astro_events ADD COLUMN {col} {data_type}")
            except sqlite3.OperationalError as e:
                print(f"Error adding {col}: {e}")
        else:
            print(f"Column {col} already exists.")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()

import sqlite3
import os

def migrate_split():
    src_db = 'inquiries.db'
    dst_db = 'moon_data.db'
    
    # Remove destination if exists to start fresh (for safety during dev)
    if os.path.exists(dst_db):
        os.remove(dst_db)
        
    conn_dst = sqlite3.connect(dst_db)
    cursor_dst = conn_dst.cursor()
    
    print("Creating tables in moon_data.db...")
    # moon_data table (including year)
    cursor_dst.execute('''
        CREATE TABLE moon_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prefecture TEXT,
            month INTEGER,
            day INTEGER,
            moon_rise TEXT,
            moon_set TEXT,
            moon_age TEXT,
            year INTEGER
        )
    ''')
    
    # astro_events table (including image_url matching code expectation)
    cursor_dst.execute('''
        CREATE TABLE astro_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            title TEXT NOT NULL,
            date_text TEXT,
            description TEXT,
            details TEXT,
            tips TEXT,
            badge TEXT,
            iso_date TEXT,
            image_url TEXT,
            is_important BOOLEAN DEFAULT 0
        )
    ''')
    
    conn_dst.commit()
    
    print("Migrating data from inquiries.db...")
    
    # Attach source database
    cursor_dst.execute(f"ATTACH DATABASE '{src_db}' AS src")
    
    # Migrate moon_data
    # We select specific columns to be safe
    print("Migrating moon_data...")
    cursor_dst.execute('''
        INSERT INTO moon_data (id, prefecture, month, day, moon_rise, moon_set, moon_age, year)
        SELECT id, prefecture, month, day, moon_rise, moon_set, moon_age, year
        FROM src.moon_data
    ''')
    
    # Migrate astro_events
    # Note: src might NOT have image_url, so we omit it from SELECT if it's missing in src
    # Based on inspection, src definitely has: id, slug, title, date_text, description, details, tips, badge, iso_date, is_important
    print("Migrating astro_events...")
    cursor_dst.execute('''
        INSERT INTO astro_events (id, slug, title, date_text, description, details, tips, badge, iso_date, is_important)
        SELECT id, slug, title, date_text, description, details, tips, badge, iso_date, is_important
        FROM src.astro_events
    ''')
    
    conn_dst.commit()
    
    # Verify counts
    count_moon_dst = cursor_dst.execute("SELECT count(*) FROM moon_data").fetchone()[0]
    count_moon_src = cursor_dst.execute("SELECT count(*) FROM src.moon_data").fetchone()[0]
    
    count_astro_dst = cursor_dst.execute("SELECT count(*) FROM astro_events").fetchone()[0]
    count_astro_src = cursor_dst.execute("SELECT count(*) FROM src.astro_events").fetchone()[0]
    
    print(f"moon_data: Source={count_moon_src}, Dest={count_moon_dst}")
    print(f"astro_events: Source={count_astro_src}, Dest={count_astro_dst}")
    
    cursor_dst.execute("DETACH DATABASE src")
    conn_dst.close()
    
    if count_moon_dst == count_moon_src and count_astro_dst == count_astro_src:
        print("Migration SUCCESS!")
    else:
        print("Migration WARNING: Counts do not match!")

if __name__ == "__main__":
    migrate_split()

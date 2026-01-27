import os
import csv
import sqlite3
import re

def migrate():
    db_path = 'inquiries.db'
    base_dir = 'data/csv_folder'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moon_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prefecture TEXT,
            month INTEGER,
            day INTEGER,
            moon_rise TEXT,
            moon_set TEXT,
            moon_age TEXT
        )
    ''')
    
    # Clear existing data to avoid duplicates if re-run
    cursor.execute('DELETE FROM moon_data')
    
    for foldername in os.listdir(base_dir):
        # Extract prefecture from folder name (e.g., "csv_folder_大阪(大阪府)")
        match = re.search(r'csv_folder_(.+)', foldername)
        if not match:
            continue
        prefecture = match.group(1)
        folder_path = os.path.join(base_dir, foldername)
        
        if not os.path.isdir(folder_path):
            continue
            
        print(f"Processing {prefecture}...")
        
        for filename in os.listdir(folder_path):
            if not filename.endswith('.csv'):
                continue
                
            # Extract month from filename (e.g., "大阪(大阪府)の月の出入り01月.csv")
            month_match = re.search(r'(\d+)月', filename)
            if not month_match:
                continue
            month = int(month_match.group(1))
            
            file_path = os.path.join(folder_path, filename)
            
            with open(file_path, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for day, row in enumerate(reader, 1):
                    cursor.execute('''
                        INSERT INTO moon_data (prefecture, month, day, moon_rise, moon_set, moon_age)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (prefecture, month, day, row['月の出'], row['月の入'], row['月齢']))
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()

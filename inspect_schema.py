import sqlite3

def inspect():
    with open('schema_pragma.txt', 'w', encoding='utf-8') as f:
        conn = sqlite3.connect('inquiries.db')
        cursor = conn.cursor()
        
        f.write("--- moon_data columns ---\n")
        cursor.execute("PRAGMA table_info(moon_data)")
        rows = cursor.fetchall()
        for row in rows:
            f.write(f"{row}\n")
        
        f.write("\n--- astro_events columns ---\n")
        cursor.execute("PRAGMA table_info(astro_events)")
        rows = cursor.fetchall()
        for row in rows:
            f.write(f"{row}\n")
            
        conn.close()

if __name__ == "__main__":
    inspect()

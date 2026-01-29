import sqlite3

def check_date_range():
    db_path = 'moon_data.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get distinct years
    years = [row[0] for row in cursor.execute("SELECT DISTINCT year FROM moon_data ORDER BY year").fetchall()]
    print(f"Available years: {years}")
    
    if not years:
        print("No data found.")
        conn.close()
        return

    min_year = years[0]
    max_year = years[-1]
    
    # Get min date
    min_date_row = cursor.execute(
        "SELECT year, month, day FROM moon_data WHERE year = ? ORDER BY month ASC, day ASC LIMIT 1", 
        (min_year,)
    ).fetchone()
    
    # Get max date
    max_date_row = cursor.execute(
        "SELECT year, month, day FROM moon_data WHERE year = ? ORDER BY month DESC, day DESC LIMIT 1", 
        (max_year,)
    ).fetchone()
    
    # Format: YYYY-MM-DD
    min_date_str = f"{min_date_row[0]}-{min_date_row[1]:02d}-{min_date_row[2]:02d}"
    max_date_str = f"{max_date_row[0]}-{max_date_row[1]:02d}-{max_date_row[2]:02d}"
    
    print(f"Min Date: {min_date_str}")
    print(f"Max Date: {max_date_str}")
    
    conn.close()

if __name__ == "__main__":
    check_date_range()

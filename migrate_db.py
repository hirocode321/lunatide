import sqlite3
from werkzeug.security import generate_password_hash

def migrate_admin():
    conn = sqlite3.connect('inquiries.db')
    cursor = conn.cursor()
    
    hashed_password = generate_password_hash('password123')
    
    # Update existing admin password to hashed version
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, 'admin'))
    
    if cursor.rowcount == 0:
        # If admin doesn't exist, insert it
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_password))
    
    conn.commit()
    conn.close()
    print("Admin password updated to hashed version successfully.")

if __name__ == "__main__":
    migrate_admin()

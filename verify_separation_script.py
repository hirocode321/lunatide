from app import app
from database import get_db, get_moon_db
import sqlite3

def verify():
    print("Verifying database separation...")
    with app.app_context():
        # Check inquiries.db
        db = get_db()
        row = db.execute("SELECT * FROM users").fetchone()
        print(f"Access inquiries.db (users): {'OK' if row else 'OK (empty)'}")
        
        # Check moon_data.db
        moon_db = get_moon_db()
        row = moon_db.execute("SELECT * FROM moon_data LIMIT 1").fetchone()
        print(f"Access moon_data.db (moon_data): {'OK' if row else 'FAIL'}")
        
        row = moon_db.execute("SELECT count(*) FROM astro_events").fetchone()
        print(f"Access moon_data.db (astro_events): Count={row[0]}")
        
    print("Verification script finished.")

if __name__ == "__main__":
    verify()

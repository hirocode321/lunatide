from app import app
from database import get_db
import sqlite3

def verify_app():
    print("Verifying app startup...")
    with app.app_context():
        print("Context pushed.")
        try:
            db = get_db()
            print("Database connected successfully.")
            
            # Test a query
            cursor = db.cursor()
            cursor.execute("SELECT 1")
            print("Query executed successfully.")
            
            # Test route handlers (simulated)
            # This implicitly tests if routes can import get_db and use it
            from routes.main import index
            # Note: index() might need request context, so we use test_client
        except Exception as e:
            print(f"Database verification failed: {e}")
            raise e

    print("Verifying request handling...")
    client = app.test_client()
    try:
        resp = client.get('/')
        if resp.status_code == 200:
            print("Index route '/' OK")
        else:
            print(f"Index route '/' returned {resp.status_code}")
            
        resp = client.get('/astro')
        if resp.status_code == 200:
            print("Astro route '/astro' OK")
        else:
            print(f"Astro route '/astro' returned {resp.status_code}")
            
    except Exception as e:
        print(f"Request verification failed: {e}")
        raise e

if __name__ == "__main__":
    verify_app()

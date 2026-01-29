import os
# Create a dummy .env file for testing if it doesn't exist
if not os.path.exists('.env'):
    with open('.env', 'w') as f:
        f.write('SECRET_KEY=test_verification_key\n')

from app import app

def verify_env_loading():
    print("Verifying .env loading...")
    # App is already imported, which should have triggered load_dotenv()
    if os.environ.get('SECRET_KEY') == 'test_verification_key':
        print("SUCCESS: SECRET_KEY loaded from .env")
    else:
        print(f"FAILURE: SECRET_KEY is {os.environ.get('SECRET_KEY')}")
        
    if app.secret_key == 'test_verification_key':
         print("SUCCESS: app.secret_key set correctly")
    else:
         print(f"FAILURE: app.secret_key is {app.secret_key}")

if __name__ == "__main__":
    verify_env_loading()
    # Clean up dummy .env
    if os.path.exists('.env') and os.environ.get('SECRET_KEY') == 'test_verification_key':
        os.remove('.env')

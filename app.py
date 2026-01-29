import os
from flask import Flask, render_template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from routes.main import main_bp
from routes.moon import moon_bp
from routes.tide import tide_bp
from routes.astro import astro_bp
from routes.admin import admin_bp

app = Flask(__name__)
# Security: Prefer env var, fallback only for dev (and ideally warn)
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    if app.debug:
        app.secret_key = 'default_insecure_dev_key'
        print("WARNING: Key 'SECRET_KEY' not found in env. Using default insecure key for development.")
    else:
        raise ValueError("No SECRET_KEY set for production application")

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(moon_bp)
app.register_blueprint(tide_bp)
app.register_blueprint(astro_bp)
app.register_blueprint(admin_bp)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.teardown_appcontext
def close_connection(exception):
    from database import close_connection
    close_connection(exception)



if __name__ == '__main__':
    # init_db()
    app.run(port=5555, debug=True)
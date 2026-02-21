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
from routes.guide import guide_bp
from routes.iss import iss_bp
from routes.spots import spots_bp
from routes.sea_spots import sea_spots_bp
from routes.gallery import gallery_bp

app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY')
debug_mode = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'

if not app.secret_key:
    if debug_mode:
        app.secret_key = 'default_insecure_dev_key'
        print("WARNING: Key 'SECRET_KEY' not found in env. Using default insecure key for development.")
    else:
        raise ValueError("No SECRET_KEY set for production application. Set SECRET_KEY environment variable.")

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(moon_bp)
app.register_blueprint(tide_bp)
app.register_blueprint(astro_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(guide_bp)
app.register_blueprint(iss_bp)
app.register_blueprint(spots_bp)
app.register_blueprint(sea_spots_bp)
app.register_blueprint(gallery_bp)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.context_processor
def inject_prefectures():
    from flask import request
    from models.functions import load_prefectures, get_today
    return {
        'prefectures': load_prefectures(),
        'pref_location': request.cookies.get('pref_location', '大阪(大阪府)'),
        'today': get_today()
    }

@app.teardown_appcontext
def close_connection(exception):
    from database import close_connection
    close_connection(exception)



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

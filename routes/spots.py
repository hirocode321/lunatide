import os
import uuid
import sqlite3
from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from werkzeug.utils import secure_filename
from models.weather import get_weather_by_coords
from models.astro_calc import get_sun_events_by_coords, get_moon_data_by_coords
from models.spots_utils import estimate_bortle_scale
from database import get_moon_db

spots_bp = Blueprint('spots', __name__)

UPLOAD_FOLDER = 'static/uploads/observation_spots'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@spots_bp.route('/spots')
def spots():
    conn = get_moon_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM observation_spots ORDER BY created_at DESC')
    rows = cursor.fetchall()
    
    spots_list = []
    for row in rows:
        spots_list.append({
            "id": row['id'],
            "name": row['name'],
            "lat": row['latitude'],
            "lng": row['longitude'],
            "note": row['description'],
            "bortle": row['bortle_scale'],
            "rating": row['rating'],
            "thumbnail": row['thumbnail_filename']
        })
    
    return render_template('spots.html', spots=spots_list, today=datetime.now().strftime('%Y-%m-%d'))

@spots_bp.route('/api/spots/add', methods=['POST'])
def add_spot():
    """新規観測スポットの登録処理"""
    name = request.form.get('name')
    lat = request.form.get('lat', type=float)
    lng = request.form.get('lng', type=float)
    note = request.form.get('note', '')
    rating = request.form.get('rating', type=int, default=3)
    
    if not name or lat is None or lng is None:
        return jsonify({"success": False, "error": "Invalid data"}), 400
        
    # ボートルスケールの自動推定
    bortle = estimate_bortle_scale(lat, lng)
    
    # サムネイル画像の処理
    thumbnail_filename = ""
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = secure_filename(f"{uuid.uuid4().hex}.{ext}")
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            thumbnail_filename = filename
            
    conn = get_moon_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO observation_spots (name, latitude, longitude, description, bortle_scale, rating, thumbnail_filename)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, lat, lng, note, bortle, rating, thumbnail_filename))
    conn.commit()
    
    return jsonify({"success": True, "message": "Spot added successfully"})

@spots_bp.route('/api/spots/weather')
def get_spot_weather():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    date_str = request.args.get('date')

    if not lat or not lng or not date_str:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        weather = get_weather_by_coords(lat, lng, date_str)
        sun = get_sun_events_by_coords(lat, lng, date_str)
        moon = get_moon_data_by_coords(lat, lng, date_str)

        return jsonify({
            "weather": weather,
            "sun": sun,
            "moon": moon
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

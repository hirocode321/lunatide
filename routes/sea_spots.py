from flask import Blueprint, render_template, request, jsonify
from database import get_moon_db
import json
import math

sea_spots_bp = Blueprint('sea_spots', __name__)

# Load port coordinates for Haversine
try:
    with open("data/region_coordinates.json", "r", encoding="utf-8") as f:
        region_coords = json.load(f)
except FileNotFoundError:
    region_coords = {}

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def find_nearest_port(lat, lng):
    min_dist = float('inf')
    nearest_pc = None
    nearest_hc = None
    
    for pc, info in region_coords.items():
        dist = calculate_distance(lat, lng, info['lat'], info['lng'])
        if dist < min_dist:
            min_dist = dist
            nearest_pc = int(pc)
            nearest_hc = int(info['hc'])
            
    if nearest_pc is not None and nearest_hc is not None:
        return f"{nearest_pc}_{nearest_hc}"
    return None

@sea_spots_bp.route('/sea_spots')
def sea_spots():
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_moon_db()
    cursor = conn.cursor()
    
    # Ignore user auth and privacy for now per user request
    spots_records = cursor.execute('''
        SELECT * FROM photo_spots 
        ORDER BY created_at DESC
    ''').fetchall()
        
    spots_data = []
    for spot in spots_records:
        spots_data.append({
            "id": spot['id'],
            "name": spot['name'],
            "lat": spot['latitude'],
            "lng": spot['longitude'],
            "note": spot['description'] or "",
            "port_id": spot['nearest_port_id'],
            "tags": spot['tags'] or "",
            "image_filename": spot['image_filename'] or ""
        })
        
    return render_template('sea_spots.html', spots=spots_data, today=today)

import os
from werkzeug.utils import secure_filename
import uuid

# Define upload folder within static
UPLOAD_FOLDER = os.path.join('static', 'uploads', 'sea_spots')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@sea_spots_bp.route('/api/sea_spots/add', methods=['POST'])
def add_spot():
    # Because we're expecting file uploads now, request might be multipart/form-data
    if request.content_type.startswith('multipart/form-data'):
        name = request.form.get('name')
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        note = request.form.get('note', '')
        tags = request.form.get('tags', '')
        
        image_filename = ""
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                # Ensure directory exists
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                # Create a unique filename
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"{uuid.uuid4().hex}.{ext}")
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                image_filename = filename
    else:
        # Fallback for old JSON requests just in case
        data = request.json or {}
        name = data.get('name')
        lat = data.get('lat')
        lng = data.get('lng')
        note = data.get('note', '')
        tags = data.get('tags', '')
        image_filename = ""
    
    if not name or lat is None or lng is None:
        return jsonify({"success": False, "error": "Invalid data"}), 400
        
    nearest_port_id = find_nearest_port(float(lat), float(lng))
    
    conn = get_moon_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO photo_spots (name, latitude, longitude, nearest_port_id, description, tags, image_filename)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, float(lat), float(lng), nearest_port_id, note, tags, image_filename))
    conn.commit()
    
    return jsonify({"success": True, "message": "Spot added successfully"})

@sea_spots_bp.route('/api/sea_spots/<int:spot_id>/tide')
def get_spot_tide(spot_id):
    date_str = request.args.get('date') # YYYY-MM-DD
    
    conn = get_moon_db()
    cursor = conn.cursor()
    spot = cursor.execute('SELECT latitude, longitude, nearest_port_id FROM photo_spots WHERE id = ?', (spot_id,)).fetchone()
    
    if not spot:
        return jsonify({"error": "Spot not found"}), 404
        
    lat, lng = spot['latitude'], spot['longitude']
    
    # Init response
    response_data = {"image_url": None, "weather": None, "sun": None, "moon": None}
    
    # 1. Tide Image URL
    if spot['nearest_port_id']:
        port_parts = spot['nearest_port_id'].split('_')
        if len(port_parts) == 2:
            pc, hc = port_parts[0], port_parts[1]
            try:
                yr, mn, dy = map(int, date_str.split("-"))
                image_url = (
                    f"https://api.tide736.net/tide_image.php?pc={pc}&hc={hc}&yr={yr}&mn={mn}&dy={dy}"
                    f"&rg=day&w=768&h=512&lc=blue&gcs=cyan&gcf=blue&ld=on&ttd=on&tsmd=on"
                )
                response_data["image_url"] = image_url
            except (ValueError, AttributeError):
                pass

    # 2. Weather & Cloud Data
    from models.weather import get_weather_by_coords
    weather_data = get_weather_by_coords(lat, lng, date_str)
    if weather_data:
        response_data["weather"] = weather_data
        
    # 3. Sun & Moon Data
    from models.astro_calc import get_sun_events_by_coords, get_moon_data_by_coords
    sun_data = get_sun_events_by_coords(lat, lng, date_str)
    moon_data = get_moon_data_by_coords(lat, lng, date_str)
    
    if sun_data:
        response_data["sun"] = sun_data
    if moon_data:
        response_data["moon"] = moon_data

    return jsonify(response_data)

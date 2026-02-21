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
            "port_id": spot['nearest_port_id']
        })
        
    return render_template('sea_spots.html', spots=spots_data, today=today)

@sea_spots_bp.route('/api/sea_spots/add', methods=['POST'])
def add_spot():
    data = request.json
    name = data.get('name')
    lat = data.get('lat')
    lng = data.get('lng')
    note = data.get('note', '')
    
    if not name or lat is None or lng is None:
        return jsonify({"success": False, "error": "Invalid data"}), 400
        
    nearest_port_id = find_nearest_port(float(lat), float(lng))
    
    conn = get_moon_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO photo_spots (name, latitude, longitude, nearest_port_id, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, float(lat), float(lng), nearest_port_id, note))
    conn.commit()
    
    return jsonify({"success": True, "message": "Spot added successfully"})

@sea_spots_bp.route('/api/sea_spots/<int:spot_id>/tide')
def get_spot_tide(spot_id):
    date_str = request.args.get('date') # YYYY-MM-DD
    
    conn = get_moon_db()
    cursor = conn.cursor()
    spot = cursor.execute('SELECT nearest_port_id FROM photo_spots WHERE id = ?', (spot_id,)).fetchone()
    
    if not spot or not spot['nearest_port_id']:
        return jsonify({"error": "No port data associated with this spot"}), 404
        
    port_parts = spot['nearest_port_id'].split('_')
    if len(port_parts) != 2:
        return jsonify({"error": "Invalid port data format"}), 500
        
    pc, hc = port_parts[0], port_parts[1]
    
    try:
        yr, mn, dy = map(int, date_str.split("-"))
    except (ValueError, AttributeError):
        return jsonify({"error": "Invalid date format"}), 400
        
    image_url = (
        f"https://api.tide736.net/tide_image.php?pc={pc}&hc={hc}&yr={yr}&mn={mn}&dy={dy}"
        f"&rg=day&w=768&h=512&lc=blue&gcs=cyan&gcf=blue&ld=on&ttd=on&tsmd=on"
    )
    
    return jsonify({"image_url": image_url})

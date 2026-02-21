"""
海辺の撮影スポット（フォトスポット）の管理および潮汐・天文データの提供を行うBlueprint。
スポットの登録、一覧表示、および特定スポットの干満情報の取得を処理します。
"""
from flask import Blueprint, render_template, request, jsonify
from database import get_moon_db
import json
import math

# 海辺の撮影地関連のルートを定義するBlueprint
sea_spots_bp = Blueprint('sea_spots', __name__)

# タイドグラフ取得に必要な、最寄りの観測所を特定するための座標データをロード
try:
    with open("data/region_coordinates.json", "r", encoding="utf-8") as f:
        region_coords = json.load(f)
except FileNotFoundError:
    region_coords = {}

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    ハバーサイン公式（Haversine formula）を用いて、地球上の2点間の距離(km)を計算します。
    最寄りの港を検索するために使用されます。
    """
    R = 6371 # 地球の半径 (km)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def find_nearest_port(lat, lng):
    """
    指定された緯度・経度から最も近い潮汐観測所（港）を特定します。
    region_coordinates.json に定義された地点と比較し、最小距離の地点のコード(pc_hc)を返します。
    """
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
    """
    海辺の撮影地マップのメイン画面を表示します。
    データベース（photo_spotsテーブル）から全ての撮影スポット情報を取得し、テンプレートへ渡します。
    """
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
    """
    地図上でクリックされた場所からの新規スポット登録処理。
    フロントエンドからのフォームデータ(multipart/form-data)を受け取り、
    名前、位置情報、メモ、複数のタグ、および作例画像のアップロードを処理・保存する。
    """
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
                # Create a unique filename using UUID to prevent naming conflicts
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
        
    # 指定された緯度・経度から最も近い潮汐観測所(港)のIDを計算（タイドグラフ取得用）
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
    """
    指定されたスポットのIDと日付から、干満グラフの画像URL、およびその場所の天気、太陽・月の情報を一括で取得するAPI。
    フロントエンドの詳細モーダルに表示するデータを集約して返す。
    """
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
    # 最寄りの港(nearest_port_id)情報を利用して、tide736.net のAPIから当該日付のタイドグラフ画像URLを生成する。
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
    # 緯度・経度と日付を元に、Open-Meteo API で対象地点の21時の天気と星空指数を取得する。
    from models.weather import get_weather_by_coords
    weather_data = get_weather_by_coords(lat, lng, date_str)
    if weather_data:
        response_data["weather"] = weather_data
        
    # 3. Sun & Moon Data
    # 同様の座標情報と日付から、日の出・日の入りの時間や、月の出・月の入り・月齢などの天文現象を天体力学的に計算する。
    from models.astro_calc import get_sun_events_by_coords, get_moon_data_by_coords
    sun_data = get_sun_events_by_coords(lat, lng, date_str)
    moon_data = get_moon_data_by_coords(lat, lng, date_str)
    
    if sun_data:
        response_data["sun"] = sun_data
    if moon_data:
        response_data["moon"] = moon_data

    return jsonify(response_data)

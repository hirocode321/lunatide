import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from database import get_moon_db
from models.astro_calc import get_moon_data
from models.weather import get_weather_info
from models.functions import moon_get_moon_images

gallery_bp = Blueprint('gallery', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@gallery_bp.route('/gallery')
def index():
    conn = get_moon_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM photo_logs ORDER BY shoot_date DESC, id DESC')
    # Fetching as dicts since row_factory isn't guaranteed per-route easily due to app context issues
    columns = [col[0] for col in cursor.description]
    photos = [dict(zip(columns, row)) for row in cursor.fetchall()]

    for p in photos:
        p['moon_image'] = moon_get_moon_images(p['moon_age']) if p['moon_age'] and p['moon_age'] != '-' else None

    return render_template('gallery.html', photos=photos)

@gallery_bp.route('/gallery/upload', methods=['POST'])
def upload():
    if 'photo' not in request.files:
        flash('ファイルが選択されていません', 'danger')
        return redirect(url_for('gallery.index'))
    
    file = request.files['photo']
    if file.filename == '':
        flash('ファイルが選択されていません', 'danger')
        return redirect(url_for('gallery.index'))
        
    if file and allowed_file(file.filename):
        # 1. Save file
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{original_filename}"
        
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'gallery')
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        
        # 2. Extract metadata
        description = request.form.get('description', '')
        equipment = request.form.get('equipment', '')
        shoot_date = request.form.get('shoot_date', datetime.today().strftime('%Y-%m-%d'))
        location = request.form.get('location', request.cookies.get('pref_location', '東京(東京都)'))
        
        # Auto-fetch Weather & Moon data
        weather_data = get_weather_info(location, shoot_date)
        weather_desc = weather_data.get('weather', '-') if weather_data else '-'
        
        moon_data = get_moon_data(location, shoot_date)
        moon_age = str(moon_data['moon_age']) if moon_data else '-'
        
        # 3. Save to DB
        conn = get_moon_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO photo_logs (filename, description, equipment, shoot_date, location, moon_age, weather)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (filename, description, equipment, shoot_date, location, moon_age, weather_desc))
        conn.commit()
        
        flash('写真をアップロードしました！', 'success')
        return redirect(url_for('gallery.index'))
        
    flash('許可されていないファイル形式です', 'danger')
    return redirect(url_for('gallery.index'))

@gallery_bp.route('/gallery/delete/<int:photo_id>', methods=['POST'])
def delete(photo_id):
    conn = get_moon_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT filename FROM photo_logs WHERE id = ?', (photo_id,))
    row = cursor.fetchone()
    if row:
        filename = row[0]
        filepath = os.path.join(current_app.root_path, 'static', 'uploads', 'gallery', filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            
        cursor.execute('DELETE FROM photo_logs WHERE id = ?', (photo_id,))
        conn.commit()
        flash('写真を削除しました', 'success')
        
    return redirect(url_for('gallery.index'))

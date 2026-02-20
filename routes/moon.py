from flask import Blueprint, render_template, request
import sqlite3
from models.functions import load_prefectures, get_today, moon_get_moon_images

moon_bp = Blueprint('moon', __name__)

@moon_bp.route('/moon')
def moon():
    prefectures = load_prefectures()
    today = get_today()
    pref_location = request.cookies.get('pref_location', '大阪(大阪府)')
    
    # Get moon data for today
    selected_date = today
    selected_date_parts = selected_date.split('-')
    year = int(selected_date_parts[0])
    month = int(selected_date_parts[1])
    day = int(selected_date_parts[2])

    from database import get_moon_db
    conn = get_moon_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT moon_rise, moon_set, moon_age FROM moon_data 
        WHERE prefecture = ? AND year = ? AND month = ? AND day = ?
    ''', (pref_location, year, month, day))
    row = cursor.fetchone()

    moon_data = None
    moon_image = "moon_00.png"

    if row:
        moon_data = {
            '月の出': row[0],
            '月の入': row[1],
            '月齢': row[2]
        }
        moon_image = moon_get_moon_images(moon_data['月齢'])

    # Weather info for today
    from models.weather import get_weather_info
    weather_info = get_weather_info(pref_location, selected_date)

    # Sun & Twilight info
    from models.astro_calc import get_sun_events
    sun_events = get_sun_events(pref_location, selected_date)

    return render_template(
        'moon_calendar.html',
        moon_image=moon_image,
        prefectures=prefectures,
        prefecture=pref_location,
        selected_date=selected_date,
        moon_data=moon_data,
        weather_info=weather_info,
        sun_events=sun_events,
        meta_description=f"{pref_location}の{selected_date}の月の出・月の入り・月齢情報と気象予測です。"
    )

@moon_bp.route('/moon_calendar', methods=['POST'])
def moon_calendar():
    prefectures = load_prefectures()
    prefecture = request.form['prefecture']
    selected_date = request.form['date']
    selected_date_parts = selected_date.split('-')
    year = int(selected_date_parts[0])
    month = int(selected_date_parts[1])
    day = int(selected_date_parts[2])

    # データベースからの読み込み
    # データベースからの読み込み
    from database import get_moon_db
    conn = get_moon_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT moon_rise, moon_set, moon_age FROM moon_data 
        WHERE prefecture = ? AND year = ? AND month = ? AND day = ?
    ''', (prefecture, year, month, day))
    row = cursor.fetchone()
    # conn.close()

    moon_data = None
    moon_image = "moon_00.png"

    if row:
        moon_data = {
            '月の出': row[0],
            '月の入': row[1],
            '月齢': row[2]
        }
        moon_image = moon_get_moon_images(moon_data['月齢'])

    # 気象情報の取得
    from models.weather import get_weather_info
    weather_info = get_weather_info(prefecture, selected_date)

    # Sun & Twilight info
    from models.astro_calc import get_sun_events
    sun_events = get_sun_events(prefecture, selected_date)

    return render_template(
        'moon_calendar.html',
        moon_image=moon_image,
        prefectures=prefectures,
        prefecture=prefecture,
        selected_date=selected_date,
        moon_data=moon_data,
        weather_info=weather_info,
        sun_events=sun_events,
        meta_description=f"{prefecture}の{selected_date}の月の出・月の入り・月齢情報と気象予測です。"
    )

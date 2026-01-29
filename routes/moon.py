from flask import Blueprint, render_template, request
import sqlite3
from models.functions import load_prefectures, get_today, moon_get_moon_images

moon_bp = Blueprint('moon', __name__)

@moon_bp.route('/moon')
def moon():
    prefectures = load_prefectures()
    today = get_today()
    return render_template('moon.html', prefectures=prefectures, today=today, meta_description="各都道府県の月の出、月の入り、月齢を検索。あなただけの夜空のリズムを調べましょう。")

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

    return render_template(
        'moon_calendar.html',
        moon_image=moon_image,
        prefectures=prefectures,
        prefecture=prefecture,
        selected_date=selected_date,
        moon_data=moon_data,
        meta_description=f"{prefecture}の{selected_date}の月の出・月の入り・月齢情報です。"
    )

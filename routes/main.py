from flask import Blueprint, render_template, request
from datetime import datetime
import calendar
import sqlite3
from models.functions import index_get_moon_images

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # デフォルトの年月は現在
    year = request.args.get('year', default=datetime.now().year, type=int)
    month = request.args.get('month', default=datetime.now().month, type=int)

    # 当日の日付
    from datetime import date
    today = date.today()

    # 月の日数と月初の曜日を計算
    cal = calendar.Calendar()
    days_in_month = list(cal.itermonthdays2(year, month))

    # データベースからの読み込み
    conn = sqlite3.connect('inquiries.db')
    cursor = conn.cursor()
    # 大阪のデータ(月齢は全国共通として扱う)
    cursor.execute('''
        SELECT day, moon_age FROM moon_data 
        WHERE prefecture = '大阪(大阪府)' AND month = ?
    ''', (month,))
    db_data = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    moon_images = []
    moon_ages = []

    for day, weekday in days_in_month:
        if day > 0 and day in db_data:
            moon_age = db_data[day]
            moon_ages.append(moon_age)
            moon_images.append(index_get_moon_images(moon_age))
        else:
            moon_ages.append(None)
            moon_images.append(None)

    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1

    return render_template(
        'index.html',
        year=year,
        month=month,
        today=today,
        days=days_in_month,
        moon_ages=moon_ages,
        moon_images=moon_images,
        next_month=next_month,
        next_year=next_year,
        prev_month=prev_month,
        prev_year=prev_year
    )

@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

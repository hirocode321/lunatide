from flask import Blueprint, render_template, request, make_response, url_for, abort, redirect
from datetime import datetime, date, timedelta
import calendar
import sqlite3
from models.functions import index_get_moon_images, get_moon_name, load_prefectures
from models.weather import get_weather_info
from database import get_moon_db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # デフォルトの年月は現在
    year = request.args.get('year', default=datetime.now().year, type=int)
    month = request.args.get('month', default=datetime.now().month, type=int)

    # 当日の日付
    today = date.today()

    # 月の日数と月初の曜日を計算
    cal = calendar.Calendar()
    days_in_month = list(cal.itermonthdays2(year, month))

    # User Preferred Location (Default: 大阪(大阪府))
    pref_location = request.cookies.get('pref_location', '大阪(大阪府)')
    all_prefectures = load_prefectures()

    # Get data for the selected location dynamically
    from models.astro_calc import get_moon_data_month
    db_data = get_moon_data_month(pref_location, year, month)

    moon_images = []
    moon_ages = []
    moon_names = []
    moon_rises = []

    for day, weekday in days_in_month:
        if day > 0 and day in db_data:
            moon_age = db_data[day]['age']
            moon_rise = db_data[day]['rise']
            moon_ages.append(moon_age)
            moon_images.append(index_get_moon_images(moon_age))
            moon_names.append(get_moon_name(moon_age))
            moon_rises.append(moon_rise)
        else:
            moon_ages.append(None)
            moon_images.append(None)
            moon_names.append(None)
            moon_rises.append(None)

    # Photography Potential Logic (Best when moon is small)
    photo_potential = []
    for age in moon_ages:
        if age is not None:
            try:
                f_age = float(age)
                # Moon Age < 5 or > 25 is generally good for stars
                photo_potential.append(f_age < 5 or f_age > 25)
            except ValueError:
                photo_potential.append(False)
        else:
            photo_potential.append(False)

    # 天文イベントの読み込み
    from database import get_moon_db
    conn = get_moon_db()
    c = conn.cursor()
    
    # 月でフィルタリング
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-31"
    db_events = c.execute("SELECT * FROM astro_events WHERE iso_date BETWEEN ? AND ?", (start_date, end_date)).fetchall()

    events_by_day = {}
    for event in db_events:
        d = datetime.fromisoformat(event['iso_date']).day
        events_by_day[d] = {
            "id": event['slug'], 
            "title": event['title'],
            "badge": event['badge'],
            "is_important": event['is_important']
        }

    # Today's Recommendation Logic
    recommendation = {
        "title": "今日のおすすめ",
        "icon": "fas fa-star",
        "text": "夜空を見上げてみましょう。"
    }
    
    # Get today's moon age if visible in current calendar context
    # Usually we want the *actual* today's recommendation, regardless of the calendar view
    # But if the user is looking at a past/future month, maybe show for that month view? 
    # The requirement says "Today's Recommendation", implying the current real-world day.
    
    today_moon_age = None
    if today.day in db_data and year == today.year and month == today.month:
        today_moon_age = db_data[today.day]['age']
    else:
        from models.astro_calc import get_moon_data
        today_info = get_moon_data(pref_location, f"{today.year}-{today.month:02d}-{today.day:02d}")
        if today_info and today_info['moon_age'] != '-':
            today_moon_age = today_info['moon_age']
            
    if today_moon_age is not None:
        try:
            age = float(today_moon_age)
            if age < 3 or age > 27:
                recommendation = {"title": "星空観測に最適", "icon": "fas fa-star", "text": "月明かりがなく、天の川や淡い星団を探す絶好のチャンスです。", "bg_class": "bg-dark text-white"}
            elif age < 7:
                recommendation = {"title": "三日月を探そう", "icon": "fas fa-moon", "text": "夕暮れの西の空に浮かぶ繊細な月を楽しめます。地球照が見えるかも？", "bg_class": "bg-primary text-white"}
            elif age < 12:
                recommendation = {"title": "クレーター観測好機", "icon": "fas fa-circle-notch", "text": "半月の頃はクレーターの影がはっきり見え、望遠鏡や双眼鏡での観測に最適です。", "bg_class": "bg-info text-dark"}
            elif age < 18:
                recommendation = {"title": "月光浴を楽しもう", "icon": "far fa-moon", "text": "明るい月が夜道を照らします。夜の散歩や、月明かりの下での読書はいかが？", "bg_class": "bg-warning text-dark"}
            else:
                recommendation = {"title": "夜空を見上げよう", "icon": "fas fa-meteor", "text": "季節の星座を探してみましょう。", "bg_class": "bg-secondary text-white"}
        except ValueError:
            pass

    # Tomorrow's Event Notification
    tomorrow = today + timedelta(days=1)
    tomorrow_iso_start = tomorrow.strftime("%Y-%m-%d")
    tomorrow_event = c.execute("SELECT * FROM astro_events WHERE iso_date LIKE ? ORDER BY is_important DESC LIMIT 1", (f"{tomorrow_iso_start}%",)).fetchone()

    # Weather Info for Today (Preferred Location)
    weather_info = get_weather_info(pref_location, today.strftime('%Y-%m-%d'))

    # Timeline Events
    from models.astro_calc import get_timeline_events
    timeline_events = get_timeline_events(pref_location, today.strftime('%Y-%m-%d'))

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
        moon_names=moon_names,
        moon_rises=moon_rises,
        next_month=next_month,
        next_year=next_year,
        prev_month=prev_month,
        prev_year=prev_year,
        events_by_day=events_by_day,
        db_events=db_events,
        recommendation=recommendation,
        tomorrow_event=tomorrow_event,
        photo_potential=photo_potential,
        weather_info=weather_info,
        timeline_events=timeline_events,
        pref_location=pref_location,
        all_prefectures=all_prefectures,
        meta_description=f"{year}年{month}月の月齢カレンダー。今日の月の満ち欠けや、注目の天体イベントをチェックして、夜空を楽しもう。"
    )

@main_bp.route('/set_location', methods=['POST'])
def set_location():
    prefecture = request.form.get('prefecture')
    next_url = request.form.get('next', url_for('main.index'))
    
    response = make_response(redirect(next_url))
    if prefecture:
        # Save location in cookie for 365 days
        response.set_cookie('pref_location', prefecture, max_age=365*24*60*60)
    return response

@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

@main_bp.route('/sitemap.xml')
def sitemap():
    # Static pages
    pages = []
    # Add static rules
    for rule in ['main.index', 'main.privacy', 'main.terms', 'astro.astro']:
        url = url_for(rule, _external=True)
        pages.append(url)

    # Dynamic pages (Astro Events)
    from database import get_moon_db
    conn = get_moon_db()
    cursor = conn.cursor()
    events = cursor.execute('SELECT slug FROM astro_events').fetchall()

    # conn.close()

    for event in events:
        url = url_for('astro.astroinfo', event=event[0], _external=True)
        pages.append(url)

    sitemap_xml = render_template('sitemap.xml', pages=pages)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

@main_bp.route('/moon/<int:year>/<int:month>/<int:day>')
def moon_detail(year, month, day):
    return redirect(url_for('moon.moon', date=f"{year}-{month:02d}-{day:02d}"))

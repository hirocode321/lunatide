"""
Skyfieldライブラリを使用して、太陽・月の出没時刻や月齢などの天文学的数値を計算するモジュール。
高精度な位置情報に基づく天文イベントを提供します。
"""
from skyfield.api import Loader, wgs84
from skyfield import almanac
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os

# 天体暦データの保存と読み込み（data/skyfieldディレクトリに保持）
load = Loader(os.path.join(os.path.dirname(__file__), '..', 'data', 'skyfield'))
eph = load('de421.bsp') # 基本的な天体位置データ
ts = load.timescale()   # 時間スケールの初期化
tz = ZoneInfo('Asia/Tokyo') # 日本標準時(JST)を使用

# カレンダー表示などに使用される都道府県別代表点の座標
PREF_COORDS = {
    "札幌(北海道)": (43.0642, 141.3469),
    "根室(北海道)": (43.3300, 145.5828),
    "青森(青森県)": (40.8244, 140.7400),
    "盛岡(岩手県)": (39.7036, 141.1525),
    "仙台(宮城県)": (38.2682, 140.8694),
    "秋田(秋田県)": (39.7186, 140.1025),
    "山形(山形県)": (38.2404, 140.3633),
    "福島(福島県)": (37.7503, 140.4675),
    "水戸(茨城県)": (36.3418, 140.4468),
    "宇都宮(栃木県)": (36.5658, 139.8836),
    "前橋(群馬県)": (36.3911, 139.0608),
    "さいたま(埼玉県)": (35.8570, 139.6490),
    "千葉(千葉県)": (35.6051, 140.1233),
    "東京(東京都)": (35.6895, 139.6917),
    "小笠原[父島](東京都)": (27.0780, 142.2045),
    "横浜(神奈川県)": (35.4478, 139.6425),
    "新潟(新潟県)": (37.9024, 139.0232),
    "富山(富山県)": (36.6953, 137.2113),
    "金沢(石川県)": (36.5947, 136.6256),
    "福井(福井県)": (36.0652, 136.2219),
    "甲府(山梨県)": (35.6639, 138.5683),
    "長野(長野県)": (36.6513, 138.1812),
    "岐阜(岐阜県)": (35.3911, 136.7222),
    "静岡(静岡県)": (34.9756, 138.3828),
    "名古屋(愛知県)": (35.1815, 136.9066),
    "津(三重県)": (34.7303, 136.5086),
    "大津(滋賀県)": (35.0145, 135.8589),
    "京都(京都府)": (35.0116, 135.7681),
    "大阪(大阪府)": (34.6937, 135.5023),
    "神戸(兵庫県)": (34.6913, 135.1830),
    "奈良(奈良県)": (34.6851, 135.8049),
    "和歌山(和歌山県)": (34.2260, 135.1675),
    "鳥取(鳥取県)": (35.5011, 134.2351),
    "松江(島根県)": (35.4723, 133.0505),
    "岡山(岡山県)": (34.6618, 133.9344),
    "広島(広島県)": (34.3966, 132.4596),
    "山口(山口県)": (34.1861, 131.4705),
    "徳島(徳島県)": (34.0658, 134.5594),
    "高松(香川県)": (34.3401, 134.0434),
    "松山(愛媛県)": (33.8417, 132.7661),
    "高知(高知県)": (33.5597, 133.5311),
    "福岡(福岡県)": (33.6066, 130.4183),
    "佐賀(佐賀県)": (33.2494, 130.2998),
    "長崎(長崎県)": (32.7448, 129.8737),
    "熊本(熊本県)": (32.7898, 130.7417),
    "大分(大分県)": (33.2382, 131.6126),
    "宮崎(宮崎県)": (31.9111, 131.4239),
    "鹿児島(鹿児島県)": (31.5602, 130.5581),
    "那覇(沖縄県)": (26.2124, 127.6809),
}

def get_sun_events(prefecture_name, date_str):
    """
    指定された都道府県の代表点における太陽イベント（日の出、日の入り、薄明）を取得します。
    """
    if prefecture_name not in PREF_COORDS:
        prefecture_name = "東京(東京都)"
        
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

    # Try cache first (fetch whole month)
    month_cache = get_sun_events_month(prefecture_name, dt.year, dt.month)
    if month_cache and dt.day in month_cache:
        return month_cache[dt.day]

    # ... fall back to single day calc if cache logic failed (should not happen with get_sun_events_month)
    lat, lon = PREF_COORDS[prefecture_name]
    location = wgs84.latlon(lat, lon)
    t0 = ts.from_datetime(dt.replace(tzinfo=tz))
    t1 = ts.from_datetime((dt + timedelta(days=1)).replace(tzinfo=tz))
    
    f = almanac.dark_twilight_day(eph, location)
    times, events = almanac.find_discrete(t0, t1, f)
    
    res = {
        'sunrise': '-', 'sunset': '-',
        'civil_dawn': '-', 'civil_dusk': '-',
        'nautical_dawn': '-', 'nautical_dusk': '-',
        'astro_dawn': '-', 'astro_dusk': '-',
        '撮影可能時間帯': '-'
    }
    
    prev_event = f(t0).item()
    for t, event in zip(times, events):
        time_str = t.astimezone(tz).strftime('%H:%M')
        if prev_event == 0 and event == 1: res['astro_dawn'] = time_str
        elif prev_event == 1 and event == 2: res['nautical_dawn'] = time_str
        elif prev_event == 2 and event == 3: res['civil_dawn'] = time_str
        elif prev_event == 3 and event == 4: res['sunrise'] = time_str
        elif prev_event == 4 and event == 3: res['sunset'] = time_str
        elif prev_event == 3 and event == 2: res['civil_dusk'] = time_str
        elif prev_event == 2 and event == 1: res['nautical_dusk'] = time_str
        elif prev_event == 1 and event == 0: res['astro_dusk'] = time_str
        prev_event = event

    if res['astro_dusk'] != '-' and res['astro_dawn'] != '-':
        res['撮影可能時間帯'] = f"18時以降から早朝まで (特に {res['astro_dusk']} 以降 ～ 翌 {res['astro_dawn']} 前)"
    elif res['astro_dusk'] != '-':
        res['撮影可能時間帯'] = f"{res['astro_dusk']} 以降"
        
    return res

def get_sun_events_by_coords(lat, lon, date_str):
    """
    指定された緯度・経度と日付から、その場所における太陽イベントを計算する。（任意座標の動的計算用）
    日の出、日の入り、および撮影可能時間帯に影響する 薄明（Twilight）の開始・終了時刻を skyfield を使って算出する。
    """
    location = wgs84.latlon(lat, lon)
    
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None
        
    t0 = ts.from_datetime(dt.replace(tzinfo=tz))
    t1 = ts.from_datetime((dt + timedelta(days=1)).replace(tzinfo=tz))
    
    f = almanac.dark_twilight_day(eph, location)
    times, events = almanac.find_discrete(t0, t1, f)
    
    res = {
        'sunrise': '-', 'sunset': '-',
        'civil_dawn': '-', 'civil_dusk': '-',
        'nautical_dawn': '-', 'nautical_dusk': '-',
        'astro_dawn': '-', 'astro_dusk': '-',
        '撮影可能時間帯': '-'
    }
    
    prev_event = f(t0).item()
    for t, event in zip(times, events):
        time_str = t.astimezone(tz).strftime('%H:%M')
        if prev_event == 0 and event == 1: res['astro_dawn'] = time_str
        elif prev_event == 1 and event == 2: res['nautical_dawn'] = time_str
        elif prev_event == 2 and event == 3: res['civil_dawn'] = time_str
        elif prev_event == 3 and event == 4: res['sunrise'] = time_str
        elif prev_event == 4 and event == 3: res['sunset'] = time_str
        elif prev_event == 3 and event == 2: res['civil_dusk'] = time_str
        elif prev_event == 2 and event == 1: res['nautical_dusk'] = time_str
        elif prev_event == 1 and event == 0: res['astro_dusk'] = time_str
        prev_event = event

    if res['astro_dusk'] != '-' and res['astro_dawn'] != '-':
        res['撮影可能時間帯'] = f"18時以降から早朝まで (特に {res['astro_dusk']} 以降 ～ 翌 {res['astro_dawn']} 前)"
    elif res['astro_dusk'] != '-':
        res['撮影可能時間帯'] = f"{res['astro_dusk']} 以降"
        
    return res

def get_moon_data(prefecture_name, date_str):
    """Calculate Moon age, moonrise, and moonset for a single day."""
    if prefecture_name not in PREF_COORDS:
        prefecture_name = "東京(東京都)"
        
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return {'moon_age': '-', 'moon_rise': '-', 'moon_set': '-'}

    # Use monthly batch/cache
    month_cache = get_moon_data_month(prefecture_name, dt.year, dt.month)
    if month_cache and dt.day in month_cache:
        day_data = month_cache[dt.day]
        return {
            'moon_age': day_data['age'],
            'moon_rise': day_data['rise'],
            'moon_set': day_data['set']
        }
        
    lat, lon = PREF_COORDS[prefecture_name]
    location = wgs84.latlon(lat, lon)
    t0 = ts.from_datetime(dt.replace(hour=0, minute=0, second=0, tzinfo=tz))
    t1 = ts.from_datetime((dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, tzinfo=tz))
    
    f = almanac.risings_and_settings(eph, eph['moon'], location)
    times, events = almanac.find_discrete(t0, t1, f)
    
    moon_rise = '-'
    moon_set = '-'
    for t, event in zip(times, events):
        time_str = t.astimezone(tz).strftime('%H:%M')
        if event == 1: moon_rise = time_str
        elif event == 0: moon_set = time_str
            
    dt_noon = dt.replace(hour=12, minute=0, second=0, tzinfo=tz)
    t_noon = ts.from_datetime(dt_noon)
    phase_degrees = almanac.moon_phase(eph, t_noon).degrees
    age = (phase_degrees / 360.0) * 29.530588
    
    return {
        'moon_age': f"{age:.1f}",
        'moon_rise': moon_rise,
        'moon_set': moon_set
    }

def get_moon_data_by_coords(lat, lon, date_str):
    """
    指定された緯度・経度と日付から、月の出、月の入り時刻、および正午時点の月齢を計算する。
    海辺の撮影地マップなど、任意の地点の天文情報を取得したい場合に利用する。
    """
    location = wgs84.latlon(lat, lon)
    
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return {'moon_age': '-', 'moon_rise': '-', 'moon_set': '-'}
        
    t0 = ts.from_datetime(dt.replace(hour=0, minute=0, second=0, tzinfo=tz))
    t1 = ts.from_datetime((dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, tzinfo=tz))
    
    f = almanac.risings_and_settings(eph, eph['moon'], location)
    times, events = almanac.find_discrete(t0, t1, f)
    
    moon_rise = '-'
    moon_set = '-'
    
    for t, event in zip(times, events):
        time_str = t.astimezone(tz).strftime('%H:%M')
        if event == 1:
            moon_rise = time_str
        elif event == 0:
            moon_set = time_str
            
    dt_noon = dt.replace(hour=12, minute=0, second=0, tzinfo=tz)
    t_noon = ts.from_datetime(dt_noon)
    phase_degrees = almanac.moon_phase(eph, t_noon).degrees
    age = (phase_degrees / 360.0) * 29.530588
    
    return {
        'moon_age': f"{age:.1f}",
        'moon_rise': moon_rise,
        'moon_set': moon_set
    }

import json
from database import get_moon_db

def _get_astro_cache(prefecture_name, year, month):
    """Retrieve astronomical data from cache if available."""
    try:
        conn = get_moon_db()
        c = conn.cursor()
        res = c.execute(
            "SELECT data_json FROM astro_cache WHERE prefecture = ? AND year = ? AND month = ?",
            (prefecture_name, year, month)
        ).fetchone()
        if res:
            return json.loads(res['data_json'])
    except Exception as e:
        print(f"Cache read error: {e}")
    return None

def _save_astro_cache(prefecture_name, year, month, data_type, data):
    """Save astronomical data to cache."""
    try:
        conn = get_moon_db()
        c = conn.cursor()
        
        # Get existing cache or create new
        existing = _get_astro_cache(prefecture_name, year, month)
        if existing is None:
            existing = {}
        
        existing[data_type] = data
        
        c.execute(
            "INSERT OR REPLACE INTO astro_cache (prefecture, year, month, data_json) VALUES (?, ?, ?, ?)",
            (prefecture_name, year, month, json.dumps(existing))
        )
        conn.commit()
    except Exception as e:
        print(f"Cache write error: {e}")

def get_moon_data_month(prefecture_name, year, month):
    """
    1ヶ月分の月の出・月の入り・月齢などのデータを一括計算（またはキャッシュから取得）します。
    """
    if prefecture_name not in PREF_COORDS:
        prefecture_name = "東京(東京都)"
        
    # Check cache first
    cached = _get_astro_cache(prefecture_name, year, month)
    if cached and 'moon' in cached:
        # Convert keys back to int if they came back as strings from JSON
        return {int(k): v for k, v in cached['moon'].items()}

    import calendar
    lat, lon = PREF_COORDS[prefecture_name]
    location = wgs84.latlon(lat, lon)
    
    _, days_in_month = calendar.monthrange(year, month)
    dt_start = datetime(year, month, 1, tzinfo=tz)
    dt_end = (dt_start + timedelta(days=days_in_month)).replace(day=1)
    
    t0 = ts.from_datetime(dt_start)
    t1 = ts.from_datetime(dt_end)
    
    f = almanac.risings_and_settings(eph, eph['moon'], location)
    times, events = almanac.find_discrete(t0, t1, f)
    
    noons = [datetime(year, month, d, 12, 0, 0, tzinfo=tz) for d in range(1, days_in_month + 1)]
    t_noons = ts.from_datetimes(noons)
    phases = almanac.moon_phase(eph, t_noons).degrees
    
    month_data = {}
    for d in range(1, days_in_month + 1):
        age_val = (phases[d-1] / 360.0) * 29.530588
        month_data[d] = {
            'age': f"{age_val:.1f}",
            'rise': '-',
            'set': '-'
        }
        
    for t, event in zip(times, events):
        local_t = t.astimezone(tz)
        if local_t.month == month and local_t.year == year:
            day = local_t.day
            time_str = local_t.strftime('%H:%M')
            if event == 1:
                month_data[day]['rise'] = time_str
            elif event == 0:
                month_data[day]['set'] = time_str
                
    # Save to cache
    _save_astro_cache(prefecture_name, year, month, 'moon', month_data)
                
    return month_data

def get_sun_events_month(prefecture_name, year, month):
    """
    1ヶ月分の太陽イベント（日の出、日の入り、薄明）を一括計算（またはキャッシュから取得）します。
    """
    if prefecture_name not in PREF_COORDS:
        prefecture_name = "東京(東京都)"
        
    cached = _get_astro_cache(prefecture_name, year, month)
    if cached and 'sun' in cached:
        return {int(k): v for k, v in cached['sun'].items()}

    import calendar
    lat, lon = PREF_COORDS[prefecture_name]
    location = wgs84.latlon(lat, lon)
    
    _, days_in_month = calendar.monthrange(year, month)
    dt_start = datetime(year, month, 1, tzinfo=tz)
    dt_end = (dt_start + timedelta(days=days_in_month)).replace(day=1)
    
    t0 = ts.from_datetime(dt_start)
    t1 = ts.from_datetime(dt_end)
    
    f = almanac.dark_twilight_day(eph, location)
    times, events = almanac.find_discrete(t0, t1, f)
    
    month_sun_data = {}
    for d in range(1, days_in_month + 1):
        month_sun_data[d] = {
            'sunrise': '-', 'sunset': '-',
            'civil_dawn': '-', 'civil_dusk': '-',
            'nautical_dawn': '-', 'nautical_dusk': '-',
            'astro_dawn': '-', 'astro_dusk': '-',
            '撮影可能時間帯': '-'
        }
    
    # We need to track the current state to know what transition happened
    # Since we are doing a whole month, we should be careful about which day the event belongs to.
    # An event at 00:30 belongs to that day.
    
    # Initial state
    current_state = f(t0).item()
    
    for t, event in zip(times, events):
        local_t = t.astimezone(tz)
        if local_t.month != month or local_t.year != year:
            continue
            
        day = local_t.day
        time_str = local_t.strftime('%H:%M')
        
        # Morning transitions
        if current_state == 0 and event == 1: month_sun_data[day]['astro_dawn'] = time_str
        elif current_state == 1 and event == 2: month_sun_data[day]['nautical_dawn'] = time_str
        elif current_state == 2 and event == 3: month_sun_data[day]['civil_dawn'] = time_str
        elif current_state == 3 and event == 4: month_sun_data[day]['sunrise'] = time_str
        # Evening transitions
        elif current_state == 4 and event == 3: month_sun_data[day]['sunset'] = time_str
        elif current_state == 3 and event == 2: month_sun_data[day]['civil_dusk'] = time_str
        elif current_state == 2 and event == 1: month_sun_data[day]['nautical_dusk'] = time_str
        elif current_state == 1 and event == 0: month_sun_data[day]['astro_dusk'] = time_str
        
        current_state = event

    # Post-process for "撮影可能時間帯"
    for d in range(1, days_in_month + 1):
        res = month_sun_data[d]
        if res['astro_dusk'] != '-' and res['astro_dawn'] != '-':
             res['撮影可能時間帯'] = f"18時以降から早朝まで (特に {res['astro_dusk']} 以降 ～ 翌 {res['astro_dawn']} 前)"
        elif res['astro_dusk'] != '-':
             res['撮影可能時間帯'] = f"{res['astro_dusk']} 以降"

    _save_astro_cache(prefecture_name, year, month, 'sun', month_sun_data)
    return month_sun_data

def _get_iss_tle():
    """
    ISSの軌道要素(TLE)を取得します。キャッシュ(24時間有効)があればそれを使用し、
    なければCelestrakから最新データを取得してキャッシュに保存します。
    """
    try:
        conn = get_moon_db()
        c = conn.cursor()
        # 24時間以内の最新キャッシュを確認
        res = c.execute(
            "SELECT tle_data FROM iss_tle_cache WHERE updated_at > datetime('now', '-1 day') ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        
        if res:
            print("ISS TLE: Using Cache")
            return res['tle_data'].splitlines()
            
        # キャッシュがない、または古い場合は取得
        print("ISS TLE: Fetching from Celestrak...")
        import requests
        stations_url = 'http://celestrak.org/NORAD/elements/stations.txt'
        response = requests.get(stations_url, timeout=10)
        if response.status_code == 200:
            lines = response.text.splitlines()
            # Find ISS
            iss_lines = []
            for i, line in enumerate(lines):
                if 'ISS (ZARYA)' in line:
                    iss_lines = lines[i:i+3]
                    break
            
            if iss_lines:
                print("ISS TLE: ISS data found and saved to cache")
                tle_str = "\n".join(iss_lines)
                c.execute("INSERT INTO iss_tle_cache (tle_data) VALUES (?)", (tle_str,))
                conn.commit()
                return iss_lines
            else:
                print("ISS TLE: 'ISS (ZARYA)' not found in stations.txt")
        else:
            print(f"ISS TLE: HTTP error {response.status_code}")
    except Exception as e:
        print(f"ISS TLE Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        
    return None

def get_timeline_events(prefecture_name, date_str):
    """
    太陽・月・薄明・ISS(国際宇宙ステーション)のイベントを統合し、時系列順に並べたタイムラインを生成します。
    """
    sun_data = get_sun_events(prefecture_name, date_str)
    moon_data = get_moon_data(prefecture_name, date_str)
    
    events = []
    
    def add_event(time_str, label, ev_type, icon):
        if time_str and time_str != '-':
            events.append({'time': time_str, 'label': label, 'type': ev_type, 'icon': icon})
            
    if sun_data:
        add_event(sun_data.get('sunset'), '日没', 'twilight', 'fas fa-sun text-warning')
        add_event(sun_data.get('astro_dusk'), '天文薄明終了 (完全な夜の始まり)', 'night_start', 'fas fa-star text-light')
        add_event(sun_data.get('astro_dawn'), '天文薄明開始 (夜明けの始まり)', 'night_end', 'fas fa-star-half-alt text-light')
        add_event(sun_data.get('sunrise'), '日の出', 'twilight', 'fas fa-sun text-warning')
        
    if moon_data:
        add_event(moon_data.get('moon_rise'), '月の出', 'moon', 'fas fa-moon text-warning')
        add_event(moon_data.get('moon_set'), '月の入', 'moon_off', 'fas fa-moon text-secondary')
        
    lat, lon = PREF_COORDS.get(prefecture_name, PREF_COORDS["東京(東京都)"])
    location = wgs84.latlon(lat, lon)
    
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        pass
    else:
        # ISS passes calculation
        try:
            iss_tle = _get_iss_tle()
            if iss_tle and len(iss_tle) >= 3:
                # Use load.tle_file compatible string or manual satellite creation
                from skyfield.api import EarthSatellite
                iss_sat = EarthSatellite(iss_tle[1], iss_tle[2], iss_tle[0], ts)
                
                t0 = ts.from_datetime(dt.replace(hour=0, minute=0, second=0, tzinfo=tz))
                t1 = ts.from_datetime((dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, tzinfo=tz))
                t, evs = iss_sat.find_events(location, t0, t1, altitude_degrees=10.0)
                
                iss_passes = []
                current_pass = None
                for ti, event in zip(t, evs):
                    is_sunlit = iss_sat.at(ti).is_sunlit(eph)
                    obs_phase = almanac.dark_twilight_day(eph, location)(ti).item()
                    is_dark = (obs_phase < 3)
                    is_visible = bool(is_sunlit and is_dark)
                    
                    if event == 0:
                        current_pass = {'start': ti.astimezone(tz), 'visible': is_visible}
                    elif event == 1 and current_pass:
                        alt, az, distance = (iss_sat - location).at(ti).altaz()
                        current_pass['max_alt'] = int(alt.degrees)
                        current_pass['visible'] = current_pass['visible'] or is_visible
                    elif event == 2 and current_pass:
                        current_pass['visible'] = current_pass['visible'] or is_visible
                        if current_pass['visible']:
                            iss_passes.append(current_pass)
                        current_pass = None
                        
                for p in iss_passes:
                    if p.get('max_alt', 0) > 20: 
                        time_str = p['start'].strftime('%H:%M')
                        add_event(time_str, f"ISS通過 (最大高度 {p['max_alt']}°)", 'iss', 'fas fa-satellite text-info')
        except Exception as e:
            print("ISS Error in timeline:", e)
            
    events.sort(key=lambda x: x['time'])
    
    # Optional: Calculate dark/light duration block if needed
    return events

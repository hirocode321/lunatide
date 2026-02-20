from skyfield.api import Loader, wgs84
from skyfield import almanac
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os

# Save ephemeris data in the data directory
load = Loader(os.path.join(os.path.dirname(__file__), '..', 'data', 'skyfield'))
eph = load('de421.bsp')
ts = load.timescale()
tz = ZoneInfo('Asia/Tokyo')

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
    if prefecture_name not in PREF_COORDS:
        prefecture_name = "東京(東京都)"
        
    lat, lon = PREF_COORDS[prefecture_name]
    location = wgs84.latlon(lat, lon)
    
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None
        
    t0 = ts.from_datetime(dt.replace(tzinfo=tz))
    t1 = ts.from_datetime((dt + timedelta(days=1)).replace(tzinfo=tz))
    
    # Using sun_twilight
    # Phases: 0=Dark, 1=Astro, 2=Nautical, 3=Civil, 4=Day
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
        # Morning transitions
        if prev_event == 0 and event == 1: res['astro_dawn'] = time_str
        elif prev_event == 1 and event == 2: res['nautical_dawn'] = time_str
        elif prev_event == 2 and event == 3: res['civil_dawn'] = time_str
        elif prev_event == 3 and event == 4: res['sunrise'] = time_str
        # Evening transitions
        elif prev_event == 4 and event == 3: res['sunset'] = time_str
        elif prev_event == 3 and event == 2: res['civil_dusk'] = time_str
        elif prev_event == 2 and event == 1: res['nautical_dusk'] = time_str
        elif prev_event == 1 and event == 0: res['astro_dusk'] = time_str
        # In summer at high latitudes, transitions skip states, e.g. 1 -> 3, but in Japan this is rare.
        
        prev_event = event

    if res['astro_dusk'] != '-' and res['astro_dawn'] != '-':
        # If dusk is before dawn logically (e.g. evening of same day, morning of next day... wait t0 to t1 is midnight to midnight of ONE DAY)
        # So 'astro_dawn' is early morning, 'astro_dusk' is evening.
        res['撮影可能時間帯'] = f"18時以降から早朝まで (特に {res['astro_dusk']} 以降 ～ 翌 {res['astro_dawn']} 前)"
    elif res['astro_dusk'] != '-':
        res['撮影可能時間帯'] = f"{res['astro_dusk']} 以降"
        
    return res

def get_moon_data(prefecture_name, date_str):
    """Calculate Moon age, moonrise, and moonset for a single day."""
    if prefecture_name not in PREF_COORDS:
        prefecture_name = "東京(東京都)"
        
    lat, lon = PREF_COORDS[prefecture_name]
    location = wgs84.latlon(lat, lon)
    
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return {'moon_age': '-', 'moon_rise': '-', 'moon_set': '-'}
        
    t0 = ts.from_datetime(dt.replace(hour=0, minute=0, second=0, tzinfo=tz))
    t1 = ts.from_datetime((dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, tzinfo=tz))
    
    # Calculate risings and settings
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
            
    # Calculate moon age at 12:00 PM JST
    dt_noon = dt.replace(hour=12, minute=0, second=0, tzinfo=tz)
    t_noon = ts.from_datetime(dt_noon)
    phase_degrees = almanac.moon_phase(eph, t_noon).degrees
    # Convert degrees (0-360) to days (0-29.53)
    # Synodic month is approx 29.530588 days
    age = (phase_degrees / 360.0) * 29.530588
    
    return {
        'moon_age': f"{age:.1f}",
        'moon_rise': moon_rise,
        'moon_set': moon_set
    }

def get_moon_data_month(prefecture_name, year, month):
    """Calculate Moon data for the entire month to be used in calendars."""
    import calendar
    
    if prefecture_name not in PREF_COORDS:
        prefecture_name = "東京(東京都)"
        
    lat, lon = PREF_COORDS[prefecture_name]
    location = wgs84.latlon(lat, lon)
    
    _, days_in_month = calendar.monthrange(year, month)
    
    # Find all risings and settings in the month
    dt_start = datetime(year, month, 1, tzinfo=tz)
    dt_end = (dt_start + timedelta(days=days_in_month)).replace(day=1) # 1st of next month
    
    t0 = ts.from_datetime(dt_start)
    t1 = ts.from_datetime(dt_end)
    
    f = almanac.risings_and_settings(eph, eph['moon'], location)
    times, events = almanac.find_discrete(t0, t1, f)
    
    # Pre-calculate moon phases for every day at 12:00 PM JST using an array
    noons = [datetime(year, month, d, 12, 0, 0, tzinfo=tz) for d in range(1, days_in_month + 1)]
    t_noons = ts.from_datetimes(noons)
    phases = almanac.moon_phase(eph, t_noons).degrees
    
    # Initialize result dictionary for 1..days_in_month
    month_data = {}
    for d in range(1, days_in_month + 1):
        age_val = (phases[d-1] / 360.0) * 29.530588
        month_data[d] = {
            'age': f"{age_val:.1f}",
            'rise': '-',
            'set': '-'
        }
        
    # Attribute the events to the appropriate day
    for t, event in zip(times, events):
        local_t = t.astimezone(tz)
        if local_t.month == month and local_t.year == year:
            day = local_t.day
            time_str = local_t.strftime('%H:%M')
            if event == 1:
                month_data[day]['rise'] = time_str
            elif event == 0:
                month_data[day]['set'] = time_str
                
    return month_data

def get_timeline_events(prefecture_name, date_str):
    """Combine sun, twilight, moon, and ISS events into a chronologically sorted timeline."""
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
        stations_url = 'http://celestrak.org/NORAD/elements/stations.txt'
        try:
            satellites = load.tle_file(stations_url)
            by_name = {sat.name: sat for sat in satellites}
            iss_sat = by_name.get('ISS (ZARYA)')
            if iss_sat:
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

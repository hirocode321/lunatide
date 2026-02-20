from flask import Blueprint, render_template, request
from skyfield.api import Loader, wgs84
from models.astro_calc import PREF_COORDS, tz, ts, eph, load
import os
from datetime import datetime, timedelta

iss_bp = Blueprint('iss', __name__)

@iss_bp.route("/iss")
def iss():
    pref_location = request.cookies.get('pref_location', '東京(東京都)')
    
    if pref_location not in PREF_COORDS:
        pref_location = "東京(東京都)"
        
    lat, lon = PREF_COORDS[pref_location]
    location = wgs84.latlon(lat, lon)
    
    # Load ISS TLE from Celestrak
    stations_url = 'http://celestrak.org/NORAD/elements/stations.txt'
    # load.tle_file will cache the file and only reload if it's too old
    satellites = load.tle_file(stations_url)
    by_name = {sat.name: sat for sat in satellites}
    iss_sat = by_name.get('ISS (ZARYA)')
    
    passes = []
    
    if iss_sat:
        # Calculate passes for the next 7 days
        now = datetime.now(tz)
        t0 = ts.from_datetime(now)
        t1 = ts.from_datetime(now + timedelta(days=7))
        
        # Determine times when the ISS is above 10 degrees altitude
        t, events = iss_sat.find_events(location, t0, t1, altitude_degrees=10.0)
        
        # events: 0=rise, 1=culminate, 2=set
        # We need to group them by pass
        current_pass = {}
        for ti, event in zip(t, events):
            time_obj = ti.astimezone(tz)
            
            # Check if ISS is illuminated by the sun
            is_sunlit = iss_sat.at(ti).is_sunlit(eph)
            # Check if observer is in darkness (0=Dark, 1=Astro, 2=Nautical)
            from skyfield import almanac
            obs_phase = almanac.dark_twilight_day(eph, location)(ti).item()
            is_dark = (obs_phase < 3)
            
            is_visible = bool(is_sunlit and is_dark)
            
            if event == 0:
                current_pass = {'start_time': time_obj, 'start_visible': is_visible}
            elif event == 1:
                # Max altitude
                alt, az, distance = (iss_sat - location).at(ti).altaz()
                current_pass['max_alt_time'] = time_obj
                current_pass['max_alt'] = int(alt.degrees)
                current_pass['max_visible'] = is_visible
            elif event == 2:
                current_pass['end_time'] = time_obj
                current_pass['end_visible'] = is_visible
                
                # We only show passes that have at least some visibility
                if current_pass.get('start_visible') or current_pass.get('max_visible') or current_pass.get('end_visible'):
                    passes.append(current_pass)
                current_pass = {}

    # Format the data for the template
    formatted_passes = []
    for p in passes:
        # We consider it a good pass if max altitude is > 30 deg
        rating = "★★★" if p.get('max_alt', 0) > 45 else ("★★☆" if p.get('max_alt', 0) > 20 else "★☆☆")
        formatted_passes.append({
            'date': p['start_time'].strftime('%Y-%m-%d'),
            'start_time': p['start_time'].strftime('%H:%M'),
            'max_alt_time': p.get('max_alt_time').strftime('%H:%M') if 'max_alt_time' in p else '-',
            'max_alt': f"{p.get('max_alt', '-')}°",
            'end_time': p['end_time'].strftime('%H:%M'),
            'rating': rating,
            'rating_val': p.get('max_alt', 0),
        })
        
    # Sort by date
    formatted_passes.sort(key=lambda x: (x['date'], x['start_time']))

    return render_template(
        'iss.html',
        pref_location=pref_location,
        passes=formatted_passes,
        all_prefectures=list(PREF_COORDS.keys())
    )

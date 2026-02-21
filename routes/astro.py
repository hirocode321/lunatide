from flask import Blueprint, render_template, request, abort
import sqlite3
from database import get_moon_db

astro_bp = Blueprint('astro', __name__)

@astro_bp.route("/astro")
def astro():
    category = request.args.get('category')
    
    from database import get_moon_db
    conn = get_moon_db()
    # conn.row_factory = sqlite3.Row  # Already set in get_db
    c = conn.cursor()
    
    query = 'SELECT * FROM astro_events ORDER BY iso_date'
    params = ()
    if category:
        query = 'SELECT * FROM astro_events WHERE badge = ? ORDER BY iso_date'
        params = (category,)
        
    raw_events = c.execute(query, params).fetchall()
    
    # Get unique badges for filter buttons
    badges = [row[0] for row in c.execute('SELECT DISTINCT badge FROM astro_events').fetchall()]
    
    # Parse and group by month
    from datetime import datetime
    grouped_events = {}
    for event in raw_events:
        dt = datetime.fromisoformat(event['iso_date'])
        month_label = f"{dt.month}月"
        if month_label not in grouped_events:
            grouped_events[month_label] = []
        
        # Add a formatted date string for the template
        event_dict = dict(event)
        event_dict['display_date'] = dt.strftime('%m月%d日')
        # Add weekday (optional but nice)
        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        event_dict['display_weekday'] = weekdays[dt.weekday()]
        
        grouped_events[month_label].append(event_dict)
    
    return render_template('astro.html', grouped_events=grouped_events, badges=badges, current_category=category)

@astro_bp.route("/astroinfo")
def astroinfo():
    slug = request.args.get('event')
    if not slug:
        abort(404)
        
    from database import get_moon_db
    conn = get_moon_db()
    # conn.row_factory = sqlite3.Row
    c = conn.cursor()
    event_data = c.execute('SELECT * FROM astro_events WHERE slug = ?', (slug,)).fetchone()
    
    # conn.close() - handled by teardown
    
    if not event_data:
        abort(404)
        
    return render_template(
        'astroinfo.html', 
        event=event_data,
        meta_description=event_data['description'],
        meta_title=f"{event_data['title']} - LunaTide"
    )

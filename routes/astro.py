from flask import Blueprint, render_template, request, abort
import sqlite3

astro_bp = Blueprint('astro', __name__)

@astro_bp.route("/astro")
def astro():
    category = request.args.get('category')
    
    conn = sqlite3.connect('inquiries.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if category:
        events = c.execute('SELECT * FROM astro_events WHERE badge = ? ORDER BY iso_date', (category,)).fetchall()
    else:
        events = c.execute('SELECT * FROM astro_events ORDER BY iso_date').fetchall()
        
    # Get unique badges for filter buttons
    badges = [row[0] for row in c.execute('SELECT DISTINCT badge FROM astro_events').fetchall()]
    
    conn.close()
    return render_template('astro.html', events=events, badges=badges, current_category=category)

@astro_bp.route("/astroinfo")
def astroinfo():
    slug = request.args.get('event')
    if not slug:
        abort(404)
        
    conn = sqlite3.connect('inquiries.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    event_data = c.execute('SELECT * FROM astro_events WHERE slug = ?', (slug,)).fetchone()
    conn.close()
    
    if not event_data:
        abort(404)
        
    return render_template(
        'astroinfo.html', 
        event=event_data,
        meta_description=event_data['description'],
        meta_title=f"{event_data['title']} - LunaTide"
    )

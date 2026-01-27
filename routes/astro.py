from flask import Blueprint, render_template, request, abort
import sqlite3

astro_bp = Blueprint('astro', __name__)

@astro_bp.route("/astro")
def astro():
    conn = sqlite3.connect('inquiries.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # 2026年のイベントだけ表示するなどフィルタリングが必要ならここで
    events = c.execute('SELECT * FROM astro_events ORDER BY iso_date').fetchall()
    conn.close()
    return render_template('astro.html', events=events)

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

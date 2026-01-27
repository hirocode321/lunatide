from flask import Blueprint, render_template, request, abort
import json

astro_bp = Blueprint('astro', __name__)

with open("data/astro_events.json", "r", encoding="utf-8") as f:
    astro_events = json.load(f)

@astro_bp.route("/astro")
def astro():
    return render_template('astro.html')

@astro_bp.route("/astroinfo")
def astroinfo():
    event_id = request.args.get('event')
    event_data = astro_events.get(event_id)
    if not event_data:
        abort(404)
    return render_template(
        'astroinfo.html', 
        event=event_data,
        meta_description=event_data.get('description', ''),
        meta_title=f"{event_data.get('title')} - LunaTide"
    )

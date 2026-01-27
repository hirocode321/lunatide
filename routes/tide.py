from flask import Blueprint, render_template, request, jsonify
import json
from datetime import datetime

tide_bp = Blueprint('tide', __name__)

# Load JSON data
with open("data/pc_code.json", "r", encoding="utf-8") as f:
    pc_code = json.load(f)
with open("data/pc_hc.json", "r", encoding="utf-8") as f:
    pc_hc = json.load(f)
with open("data/region_coordinates.json", "r", encoding="utf-8") as f:
    region_coords = json.load(f)

def calculate_distance(lat1, lon1, lat2, lon2):
    import math
    # Simple hauling distance formula (good enough for this)
    R = 6371 # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@tide_bp.route("/tide")
def tide():
    return render_template(
        "tide.html",
        pc_code=pc_code,
        today=datetime.now().strftime("%Y-%m-%d"),
        meta_description="全国の干潮・満潮情報をグラフで確認。現在地から最寄りの港を自動で見つけることも可能です。"
    )

@tide_bp.route("/get_ports/<int:pc>")
def get_ports(pc):
    ports = pc_hc.get(str(pc), {}).get("ports", {})
    return jsonify(ports)

@tide_bp.route("/get_image_url", methods=["POST"])
def get_image_url():
    data = request.json
    pc = data.get("pc")
    hc = data.get("hc")
    date = data.get("date")

    try:
        yr, mn, dy = map(int, date.split("-"))
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    image_url = (
        f"https://api.tide736.net/tide_image.php?pc={pc}&hc={hc}&yr={yr}&mn={mn}&dy={dy}"
        f"&rg=day&w=768&h=512&lc=blue&gcs=cyan&gcf=blue&ld=on&ttd=on&tsmd=on"
    )
    return jsonify({"image_url": image_url})

@tide_bp.route("/get_nearest_port", methods=["POST"])
def get_nearest_port():
    data = request.json
    user_lat = data.get("lat")
    user_lng = data.get("lng")

    if user_lat is None or user_lng is None:
        return jsonify({"error": "Missing coordinates"}), 400

    min_dist = float('inf')
    nearest_pc = None
    nearest_hc = None

    for pc, info in region_coords.items():
        dist = calculate_distance(user_lat, user_lng, info['lat'], info['lng'])
        if dist < min_dist:
            min_dist = dist
            nearest_pc = int(pc)
            nearest_hc = int(info['hc'])

    return jsonify({"pc": nearest_pc, "hc": nearest_hc})

from flask import Blueprint, render_template, request, jsonify
import json
from datetime import datetime

tide_bp = Blueprint('tide', __name__)

# Load JSON data
with open("data/pc_code.json", "r", encoding="utf-8") as f:
    pc_code = json.load(f)
with open("data/pc_hc.json", "r", encoding="utf-8") as f:
    pc_hc = json.load(f)

@tide_bp.route("/tide")
def tide():
    return render_template(
        "tide.html",
        pc_code=pc_code,
        today=datetime.now().strftime("%Y-%m-%d"),
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

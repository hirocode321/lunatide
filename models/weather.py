import requests
from datetime import datetime
import json

# 47都道府県の庁舎所在地（代表点）の座標
PREFECTURE_COORDS = {
    "札幌(北海道)": {"lat": 43.06417, "lng": 141.34694},
    "根室(北海道)": {"lat": 43.3301, "lng": 145.5828}, # 追加
    "青森(青森県)": {"lat": 40.82444, "lng": 140.74},
    "盛岡(岩手県)": {"lat": 39.70361, "lng": 141.1525},
    "仙台(宮城県)": {"lat": 38.26889, "lng": 140.87194},
    "秋田(秋田県)": {"lat": 39.71861, "lng": 140.1025},
    "山形(山形県)": {"lat": 38.24056, "lng": 140.36333},
    "福島(福島県)": {"lat": 37.75, "lng": 140.46778},
    "水戸(茨城県)": {"lat": 36.34139, "lng": 140.44667},
    "宇都宮(栃木県)": {"lat": 36.56583, "lng": 139.88361},
    "前橋(群馬県)": {"lat": 36.39111, "lng": 139.06083},
    "さいたま(埼玉県)": {"lat": 35.85694, "lng": 139.64889},
    "千葉(千葉県)": {"lat": 35.60472, "lng": 140.12333},
    "東京(東京都)": {"lat": 35.68944, "lng": 139.69167},
    "小笠原[父島](東京都)": {"lat": 27.0947, "lng": 142.1914}, # 追加
    "横浜(神奈川県)": {"lat": 35.44778, "lng": 139.6425},
    "新潟(新潟県)": {"lat": 37.90222, "lng": 139.02361},
    "富山(富山県)": {"lat": 36.69528, "lng": 137.21139},
    "金沢(石川県)": {"lat": 36.59444, "lng": 136.62556},
    "福井(福井県)": {"lat": 36.06528, "lng": 136.22194},
    "甲府(山梨県)": {"lat": 35.66389, "lng": 138.56833},
    "長野(長野県)": {"lat": 36.65139, "lng": 138.18111},
    "岐阜(岐阜県)": {"lat": 35.39111, "lng": 136.72222},
    "静岡(静岡県)": {"lat": 34.97694, "lng": 138.38306},
    "名古屋(愛知県)": {"lat": 35.18028, "lng": 136.90667},
    "津(三重県)": {"lat": 34.73028, "lng": 136.50861},
    "大津(滋賀県)": {"lat": 35.00444, "lng": 135.86833},
    "京都(京都府)": {"lat": 35.02139, "lng": 135.75556},
    "大阪(大阪府)": {"lat": 34.68639, "lng": 135.52},
    "神戸(兵庫県)": {"lat": 34.69139, "lng": 135.18306},
    "奈良(奈良県)": {"lat": 34.68528, "lng": 135.83278},
    "和歌山(和歌山県)": {"lat": 34.22611, "lng": 135.1675},
    "鳥取(鳥取県)": {"lat": 35.50361, "lng": 134.23833},
    "松江(島根県)": {"lat": 35.47222, "lng": 133.05056},
    "岡山(岡山県)": {"lat": 34.66167, "lng": 133.935},
    "広島(広島県)": {"lat": 34.39639, "lng": 132.45944},
    "山口(山口県)": {"lat": 34.18583, "lng": 131.47139},
    "徳島(徳島県)": {"lat": 34.06583, "lng": 134.55944},
    "高松(香川県)": {"lat": 34.34028, "lng": 134.04333},
    "松山(愛媛県)": {"lat": 33.84167, "lng": 132.76611},
    "高知(高知県)": {"lat": 33.55972, "lng": 133.53111},
    "福岡(福岡県)": {"lat": 33.60639, "lng": 130.41806},
    "佐賀(佐賀県)": {"lat": 33.24944, "lng": 130.29889},
    "長崎(長崎県)": {"lat": 32.74472, "lng": 129.87361},
    "熊本(熊本県)": {"lat": 32.78917, "lng": 130.74167},
    "大分(大分県)": {"lat": 33.23806, "lng": 131.6125},
    "宮崎(宮崎県)": {"lat": 31.91111, "lng": 131.42389},
    "鹿児島(鹿児島県)": {"lat": 31.56028, "lng": 130.55806},
    "那覇(沖縄県)": {"lat": 26.2125, "lng": 127.68111}
}

WEATHER_CODE_MAP = {
    0: "快晴",
    1: "晴れ",
    2: "晴れ時々曇り",
    3: "曇り",
    45: "霧",
    48: "着氷性の霧",
    51: "小雨 (霧雨)",
    53: "雨 (中)",
    55: "強い雨 (霧雨)",
    61: "小雨",
    63: "雨",
    65: "激しい雨",
    71: "小雪",
    73: "雪",
    75: "激しい雪",
    77: "霧雪",
    80: "にわか雨 (弱)",
    81: "にわか雨 (中)",
    82: "激しいにわか雨",
    85: "にわか雪 (弱)",
    86: "にわか雪 (強)",
    95: "雷雨",
    96: "雷雨 (小霰)",
    99: "雷雨 (大霰)"
}

def get_weather_info(prefecture, date_str):
    """
    指定された都道府県と日付の天気情報（雲量、天気内容）を取得する。
    Open-Meteo APIを使用し、SQLiteデータベースに一時キャッシュする。
    """
    coords = PREFECTURE_COORDS.get(prefecture)
    if not coords:
        return None

    try:
        from database import get_moon_db
        conn = get_moon_db()
        cursor = conn.cursor()

        # 1. キャッシュの確認 (3時間以内のデータか)
        cursor.execute('''
            SELECT data_json, updated_at FROM weather_cache 
            WHERE prefecture = ? AND date_str = ?
        ''', (prefecture, date_str))
        cached = cursor.fetchone()
        
        if cached:
            # updated_at is stored as string 'YYYY-MM-DD HH:MM:SS'
            updated_at = datetime.strptime(cached['updated_at'] if isinstance(cached, sqlite3.Row) else cached[1], '%Y-%m-%d %H:%M:%S')
            # dict response is cached['data_json'] or cached[0]
            data_json = cached['data_json'] if isinstance(cached, sqlite3.Row) else cached[0]
            
            if (datetime.now() - updated_at).total_seconds() < 3 * 3600: # 3 hours
                return json.loads(data_json)

        # 2. API呼び出し (キャッシュがない、または古い場合)
        # 日付が今日から11日以内なら予報、それ以外ならアーカイブ
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        diff_days = (target_date - today).days

        if 0 <= diff_days <= 11:
            # 予報 API (JMAモデル)
            url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lng']}&hourly=cloud_cover,weather_code&models=jma&start_date={date_str}&end_date={date_str}&timezone=Asia%2FTokyo"
        else:
            # 歴史的データ API
            url = f"https://archive-api.open-meteo.com/v1/archive?latitude={coords['lat']}&longitude={coords['lng']}&start_date={date_str}&end_date={date_str}&hourly=cloud_cover,weather_code&timezone=Asia%2FTokyo"

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "hourly" in data:
            # 夜間（21時頃）の雲量を代表値として取得
            cloud_covers = data["hourly"].get("cloud_cover", [])
            weather_codes = data["hourly"].get("weather_code", [])
            
            # 天体観測に重要な21時のデータ（インデックス21）を取得
            idx = 21 if len(cloud_covers) > 21 else (len(cloud_covers) - 1)
            
            if idx >= 0:
                cloud_pct = cloud_covers[idx]
                code = weather_codes[idx]
                
                # 星空指数 (0 - 100) の計算
                # 基本は (100 - 雲量) だが、悪天候の場合は下げる
                starry_index = max(0, 100 - cloud_pct)
                if code >= 50: # 雨、雪など
                    starry_index = 0
                elif code in [45, 48]: # 霧
                    starry_index = min(starry_index, 20)
                elif code == 3: # 完全に曇り
                    starry_index = min(starry_index, 10)
                elif code == 2: # 晴れ時々曇り
                    starry_index = min(starry_index, 60)

                # 天気アイコンの設定 (FontAwesome)
                if code <= 1:
                    icon_class = "fas fa-sun text-warning"
                elif code == 2:
                    icon_class = "fas fa-cloud-sun text-warning"
                elif code in [3, 45, 48]:
                    icon_class = "fas fa-cloud text-secondary"
                elif 50 <= code <= 69 or 80 <= code <= 82:
                    icon_class = "fas fa-umbrella text-info"
                elif 70 <= code <= 79 or 85 <= code <= 86:
                    icon_class = "fas fa-snowman text-light"
                elif code >= 90:
                    icon_class = "fas fa-bolt text-danger"
                else:
                    icon_class = "fas fa-cloud-sun text-secondary"
                
                result = {
                    "cloud_cover": cloud_pct,
                    "condition": WEATHER_CODE_MAP.get(code, "不明"),
                    "starry_index": starry_index,
                    "icon_class": icon_class,
                    "time": "21:00"
                }

                # 3. キャッシュの更新
                import sqlite3 # ensure imported for Error handling if needed
                try:
                    cursor.execute('''
                        INSERT INTO weather_cache (prefecture, date_str, data_json, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(prefecture, date_str) 
                        DO UPDATE SET data_json = excluded.data_json, updated_at = CURRENT_TIMESTAMP
                    ''', (prefecture, date_str, json.dumps(result)))
                    conn.commit()
                except Exception as db_e:
                    print(f"Weather Cache DB Error: {db_e}")

                return result

    except Exception as e:
        print(f"Weather API/Cache Error: {e}")
    
    return None

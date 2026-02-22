import csv
from datetime import date
import random,string
import sqlite3


# 統一された月齢画像取得関数
def get_moon_age_image(moon_age):
    try:
        moon_age = float(moon_age)
        # 0 <= moon_age <= 30 の範囲で画像を選択
        # 画像ファイルは moon_00.png ~ moon_30.png を想定
        if moon_age < 0: moon_age = 0
        if moon_age > 30: moon_age = 30
        
        image_index = int(round(moon_age))
        return f"images/moon_{image_index:02d}.png"
    except (ValueError, TypeError):
        return "images/moon_00.png"

# 互換性のためのエイリアス（必要に応じて）
index_get_moon_images = get_moon_age_image
moon_get_moon_images = get_moon_age_image

def get_moon_name(moon_age):
    """月齢に対応する伝統的な和名を返す"""
    try:
        age = round(float(moon_age))
        if age == 0: return "新月"
        if age == 3: return "三日月"
        if age == 7: return "上弦の月"
        if age == 13: return "十三夜"
        if age == 15: return "満月"
        if age == 16: return "十六夜"
        if age == 17: return "立待月"
        if age == 18: return "居待月"
        if age == 19: return "寝待月"
        if age == 20: return "更待月"
        if age == 23: return "下弦の月"
        if age == 26: return "有明の月"
        if age == 30: return "三十日月"
        return None
    except (ValueError, TypeError):
        return None
    
# 都道府県リストを取得する関数
def load_prefectures():
    with open('data/pref_name.csv', encoding='utf-8') as f:
        return [row['pref_name'] for row in csv.DictReader(f)]

# 今日の日付を取得
def get_today():
    return date.today().strftime('%Y-%m-%d')

# セッションを作る。CSRF。
n = random.randint(10,20)
def randomname(n):
    randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
    return ''.join(randlst)
    
def init_db():
    # Initialize inquiries.db
    conn = sqlite3.connect('inquiries.db')
    cursor = conn.cursor()

    # inquiries テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            age INTEGER,
            content TEXT NOT NULL
        )
    ''')
    
    # users テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    # サンプルデータを挿入（適切なハッシュ化を行う）
    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash('password123')
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
                   ('admin', hashed_password))
    conn.commit()
    conn.close()

    # Initialize moon_data.db
    conn_moon = sqlite3.connect('moon_data.db')
    cursor_moon = conn_moon.cursor()

    # astro_events テーブル
    cursor_moon.execute('''
        CREATE TABLE IF NOT EXISTS astro_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            title TEXT NOT NULL,
            date_text TEXT,
            description TEXT,
            details TEXT,
            tips TEXT,
            badge TEXT,
            iso_date TEXT,
            image_url TEXT,
            is_important BOOLEAN DEFAULT 0,
            direction TEXT,
            time_range TEXT,
            altitude TEXT,
            viewing_mode TEXT,
            visibility_score INTEGER
        )
    ''')

    # weather_cache テーブル
    cursor_moon.execute('''
        CREATE TABLE IF NOT EXISTS weather_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prefecture TEXT NOT NULL,
            date_str TEXT NOT NULL,
            data_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(prefecture, date_str)
        )
    ''')

    # astro_cache テーブル (月単位の計算結果キャッシュ)
    cursor_moon.execute('''
        CREATE TABLE IF NOT EXISTS astro_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prefecture TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            data_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(prefecture, year, month)
        )
    ''')

    # iss_tle_cache テーブル (ISSの軌道要素キャッシュ)
    cursor_moon.execute('''
        CREATE TABLE IF NOT EXISTS iss_tle_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tle_data TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # photo_logs テーブル
    cursor_moon.execute('''
        CREATE TABLE IF NOT EXISTS photo_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            description TEXT,
            equipment TEXT,
            shoot_date TEXT NOT NULL,
            location TEXT,
            moon_age TEXT,
            weather TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # users テーブル
    cursor_moon.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # photo_spots テーブル (海辺の撮影地用)
    cursor_moon.execute('''
        CREATE TABLE IF NOT EXISTS photo_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            nearest_port_id TEXT,
            is_private BOOLEAN DEFAULT 0,
            description TEXT,
            tags TEXT,
            image_filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # observation_spots テーブル (観測スポット用)
    cursor_moon.execute('''
        CREATE TABLE IF NOT EXISTS observation_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            description TEXT,
            bortle_scale INTEGER,
            rating INTEGER DEFAULT 3,
            thumbnail_filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn_moon.commit()
    conn_moon.close()

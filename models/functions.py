import csv
from datetime import date
import random,string
import sqlite3

def index_get_moon_images(moon_age):
    # 月齢に応じた画像の決定
    # 月齢が1から7の範囲で `moon_01.png` から `moon_07.png` などを返す
    try:
        moon_age = float(moon_age)  # 月齢が文字列として読み込まれるので、数値に変換
        moon_image = f"images/moon_{int(moon_age):02d}.png"  # 画像ファイル名の作成
        return moon_image
    except ValueError:
        return None  # 月齢が無効な場合、画像なし
    
# 月齢に対応する画像名を返す関数
def moon_get_moon_images(moon_age):
    try:
        moon_age = float(moon_age)
        if 0.0 <= moon_age <= 30.0:
            image_index = int(moon_age)  # moon_00.png から moon_30.png の画像を選ぶ
        else:
            image_index = 0  # 不正な月齢の場合のデフォルト画像
        return f"moon_{image_index:02d}.png"
    except ValueError:
        return "moon_00.png"  # エラーハンドリング時のデフォルト画像

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
    conn = sqlite3.connect('inquiries.db')
    cursor = conn.cursor()

    # inquiries テーブル（既存）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            age INTEGER,
            content TEXT NOT NULL
        )
    ''')

    # users テーブル（新規追加）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    # サンプルデータを挿入（必要に応じて）
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
                   ('admin', 'password123'))
    conn.commit()
    conn.close()

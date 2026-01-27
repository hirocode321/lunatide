import json
import sqlite3
import os

def migrate():
    # 1. データベース接続
    conn = sqlite3.connect('inquiries.db')
    cursor = conn.cursor()

    # テーブルを再作成するために既存のテーブルを削除
    cursor.execute("DROP TABLE IF EXISTS astro_events")
    conn.commit()
    conn.close()

    # init_db で最新のスキーマでテーブル作成
    from models.functions import init_db
    init_db()

    conn = sqlite3.connect('inquiries.db')
    cursor = conn.cursor()

    # 2. JSONデータの読み込み
    json_path = "data/astro_events.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        events = json.load(f)

    # 3. データの挿入
    for event_id, info in events.items():
        # event_id を slug として使用
        slug = event_id
        
        cursor.execute('''
            INSERT INTO astro_events (slug, title, date_text, description, details, tips, badge, iso_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            slug,
            info['title'],
            info['date'],
            info['description'],
            info['details'],
            info['tips'],
            info['badge'],
            info['iso_date']
        ))
        print(f"Imported: {info['title']} (slug: {slug})")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()

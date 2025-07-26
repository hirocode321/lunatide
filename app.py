from datetime import date, datetime
import calendar
import csv
import json
import os
import random
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, abort, flash

from models.functions import index_get_moon_images, moon_get_moon_images, load_prefectures, get_today, randomname, init_db

app = Flask(__name__)

app.secret_key = 'your_secret_key'

# セッションを作る。CSRF。
n = random.randint(10,20)

# JSONデータを読み込み
with open("data/pc_code.json", "r", encoding="utf-8") as f:
    pc_code = json.load(f)
with open("data/pc_hc.json", "r", encoding="utf-8") as f:
    pc_hc = json.load(f)


# -------------------------------------------------------------------
### カレンダー件ホーム画面

@app.route('/')
def index():
    # デフォルトの年月は現在
    year = request.args.get('year', default=datetime.now().year, type=int)
    month = request.args.get('month', default=datetime.now().month, type=int)

    # 当日の日付
    today = date.today()

    # 月の日数と月初の曜日を計算
    cal = calendar.Calendar()
    days_in_month = list(cal.itermonthdays2(year, month))  # (日付, 曜日) のタプルのリスト

    # CSVファイルの読み込み
    csv_months = f"{month:02d}"  # 月をゼロ埋め（例: 1 -> 01）
    csv_path = f"data/csv_folder/csv_folder_大阪(大阪府)/大阪(大阪府)の月の出入り{csv_months}月.csv" # 月齢は地域差がないため大阪で設定
    moon_images = []
    moon_ages = []

    if os.path.exists(csv_path):
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)  # CSVデータをリスト化
            for day, weekday in days_in_month:
                if day > 0 and len(data) >= day:  # 有効な日付とデータが存在する場合
                    moon_age = data[day - 1]['月齢'].strip()  # CSVデータから月齢を取得
                    moon_ages.append(moon_age)  # 月齢データを追加
                    moon_images.append(index_get_moon_images(moon_age))  # 月齢画像を追加
                else:
                    moon_ages.append(None)
                    moon_images.append(None)  # 月齢データがない場合
    else:
        moon_images = [None for _ in days_in_month]  # CSVが存在しない場合
        moon_ages = [None for _ in days_in_month]  # 月齢データがない場合

    # 次月と前月の計算
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1

    return render_template(
        'index.html',
        year=year,
        month=month,
        today=today,
        days=days_in_month,
        moon_ages=moon_ages,
        moon_images=moon_images,
        next_month=next_month,
        next_year=next_year,
        prev_month=prev_month,
        prev_year=prev_year
    )



# -------------------------------------------------------------------
### 月の出入りのページ

@app.route('/moon')
def moon():
    prefectures = load_prefectures()
    today = get_today()
    return render_template('moon.html', prefectures=prefectures, today=today)

@app.route('/moon_calendar', methods=['POST'])
def moon_calendar():
    prefectures = load_prefectures()
    prefecture = request.form['prefecture']
    selected_date = request.form['date']

    # 月と日を抽出
    month = selected_date.split('-')[1]
    day = int(selected_date.split('-')[2])

    # 対応するCSVファイルを読み込む
    csv_path = f"data/csv_folder/csv_folder_{prefecture}/{prefecture}の月の出入り{month.zfill(2)}月.csv"
    moon_data = None
    moon_image = "moon_00.png"

    if os.path.exists(csv_path):
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i == day - 1:  # 日にちのインデックスに対応
                    moon_data = row
                    moon_image = moon_get_moon_images(moon_data['月齢'])
                    break

    return render_template(
        'moon_calendar.html',
        moon_image=moon_image,
        prefectures=prefectures,
        prefecture=prefecture,
        selected_date=selected_date,
        moon_data=moon_data
    )


# -------------------------------------------------------------------
### 潮の満ち引きのページ

@app.route("/tide")
def tide():
    return render_template(
        "tide.html",
        pc_code=pc_code,
        today=datetime.now().strftime("%Y-%m-%d"),
    )

@app.route("/get_ports/<int:pc>")
def get_ports(pc):
    ports = pc_hc.get(str(pc), {}).get("ports", {})
    return jsonify(ports)

@app.route("/get_image_url", methods=["POST"])
def get_image_url():
    data = request.json
    pc = data.get("pc")
    hc = data.get("hc")
    date = data.get("date")

    # 日付のフォーマットを検証
    try:
        yr, mn, dy = map(int, date.split("-"))
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    # 画像URLを生成
    image_url = (
        f"https://api.tide736.net/tide_image.php?pc={pc}&hc={hc}&yr={yr}&mn={mn}&dy={dy}"
        f"&rg=day&w=768&h=512&lc=blue&gcs=cyan&gcf=blue&ld=on&ttd=on&tsmd=on"
    )
    return jsonify({"image_url": image_url})


# -------------------------------------------------------------------
### 天文情報のページ（ここは未完成）

@app.route("/astro")
def astro():
    return render_template('astro.html')

@app.route("/info")
def info():
    return render_template('info.html')


# -------------------------------------------------------------------
### お問い合わせのページ

@app.route("/contact", methods=["GET","POST"])
def contact():
    
    if request.method == 'POST':
        # 入力データをセッションに保存
        session['form_data'] = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'age': request.form.get('age'),
            'content': request.form.get('content')
        }

        # 必須項目チェック
        errors = []
        
        if not session['form_data']['name'] or not session['form_data']['email'] :
            errors.append("名前とメールアドレスは必須です。")
        
        if session['form_data']['age']:
            if int(session['form_data']['age']) < 0:
                errors.append("年齢は0歳以上でお願いします。")
    
        if errors:
            session['error'] = errors
            return redirect(url_for('contact'))
        
        return redirect(url_for('confirm'))
    
    # GETメソッド
    # 空の辞書を作成
    temp = {}
    errors = None
    # セッションにform_dataがあれば
    if 'form_data' in session:
        # セッションを復元
        temp = session['form_data']
        session.pop('form_data', None)
    if 'error' in session:
        # セッションを復元
        errors = session['error']
        session.pop('error', None)
    
    return render_template('contact.html', error=None, form_data=temp, errors=errors)

# ルート: 確認画面
@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    if 'form_data' not in session:
        return redirect(url_for('contact'))
    
    if request.method == 'POST':
        # データベースに保存
        conn = sqlite3.connect('inquiries.db')
        cursor = conn.cursor()
        form_data = session['form_data']

        cursor.execute('''
            INSERT INTO inquiries (name, email, age, content)
            VALUES (?, ?, ?, ?)
        ''', (form_data['name'], form_data['email'] ,form_data['age'], form_data['content']))
        conn.commit()
        conn.close()
        session.pop('form_data', None)
        return redirect(url_for('complete'))
    
    return render_template('confirm.html', form_data=session['form_data'])

# ルート: 完了画面
@app.route('/complete')
def complete():
    #flash('お問い合わせありがとうございました。', 'success')
    return render_template('complete.html')


# -------------------------------------------------------------------
### データベース管理画面のページ

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # SQLiteで認証を行う
        conn = sqlite3.connect('inquiries.db')
        cursor = conn.cursor()

        # データベースからユーザー情報を取得
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        # ユーザーが存在し、パスワードが一致するか確認
        if user and user[0] == password:  # 実際にはパスワードのハッシュを確認する
            session['logged_in'] = True
            session['username'] = username
            flash('ログイン成功！', 'success')
            return redirect(url_for('db_show'))
        else:
            flash('ユーザー名またはパスワードが間違っています。', 'danger')

    # GETメソッド
    return render_template('login.html')


# ログアウト
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    #flash('ログアウトしました。', 'info')
    return redirect(url_for('login'))

# データベース表示 (認証が必要)
@app.route('/database')
def db_show():
    if not session.get('logged_in'):
        flash('このページを表示するにはログインが必要です。', 'warning')
        return redirect(url_for('login'))
    
    # データベースに接続する
    conn = sqlite3.connect('inquiries.db')
    c = conn.cursor()
    db_datas = [row for row in c.execute('SELECT * FROM inquiries')]
    conn.close()
    return render_template('database.html', db_datas=db_datas)

@app.route('/manage/<int:id>', methods=['GET', 'POST'])
def deleting_record(id):
    if not session.get('logged_in'):
        flash('このページを表示するにはログインが必要です。', 'warning')
        return redirect(url_for('login'))

    # データベースに接続
    conn = sqlite3.connect('inquiries.db')
    c = conn.cursor()
    db_data = list(c.execute('SELECT * FROM inquiries WHERE id = ?', (id,)))
    conn.close()

    if request.method == 'GET':
        # セッションにトークンがなければ生成
        if 'token' not in session:
            csrf_token = randomname(n)  # 適切な長さのトークンを生成
            session['token'] = csrf_token
        else:
            csrf_token = session['token']  # 既存のトークンを利用
        print(f'   get:  csrf_token = {csrf_token}')
        print(f'   get:  session_token = {session["token"]}')
        return render_template('manage.html', db_data=db_data, csrf_token=csrf_token)

    elif request.method == 'POST':
        # CSRFトークンの検証
        form_token = request.form.get('csrf_token')
        session_token = session.pop('token', None)  # 検証後、セッションから削除
        print(f'   post:  form_token = {form_token}')
        print(f'   post:  session_token = {session_token}')

        if not form_token or form_token != session_token:
            abort(403)  # トークンが不一致の場合は403エラー

        # トークンが一致したら削除処理
        conn = sqlite3.connect('inquiries.db')
        c = conn.cursor()
        c.execute('DELETE FROM inquiries WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        flash(f'ID {id} を削除しました。', 'success')
        return redirect('/database')


# -------------------------------------------------------------------


# プライバシーポリシー
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


# 利用規約
@app.route('/terms')
def terms():
    return render_template('terms.html')
    

# -------------------------------------------------------------------


"""
if __name__ == '__main__':
    init_db()
    app.run(port=5555, debug=True)
"""
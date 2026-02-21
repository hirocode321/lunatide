from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_moon_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_moon_db()
        cursor = conn.cursor()
        
        user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user:
            flash('ユーザー名が既に存在します。別の名前を使用してください。', 'warning')
            return redirect(url_for('auth.signup'))
            
        password_hash = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        # conn.close()
        
        flash('登録が完了しました！ログインしてください。', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_moon_db()
        cursor = conn.cursor()
        
        user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        # conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('ログインしました。', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('ログインに失敗しました。ユーザー名かパスワードが間違っています。', 'danger')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('ログアウトしました。', 'info')
    return redirect(url_for('main.index'))

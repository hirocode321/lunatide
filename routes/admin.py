from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
import sqlite3
import random
from models.functions import randomname, n
from werkzeug.security import check_password_hash

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/contact", methods=["GET","POST"])
def contact():
    if request.method == 'POST':
        session['form_data'] = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'age': request.form.get('age'),
            'content': request.form.get('content')
        }
        errors = []
        if not session['form_data']['name'] or not session['form_data']['email'] :
            errors.append("名前とメールアドレスは必須です。")
        if session['form_data']['age']:
            if int(session['form_data']['age']) < 0:
                errors.append("年齢は0歳以上でお願いします。")
        if errors:
            session['error'] = errors
            return redirect(url_for('admin.contact'))
        return redirect(url_for('admin.confirm'))
    
    temp = {}
    errors = None
    if 'form_data' in session:
        temp = session['form_data']
        session.pop('form_data', None)
    if 'error' in session:
        errors = session['error']
        session.pop('error', None)
    return render_template('contact.html', error=None, form_data=temp, errors=errors)

@admin_bp.route('/confirm', methods=['GET', 'POST'])
def confirm():
    if 'form_data' not in session:
        return redirect(url_for('admin.contact'))
    if request.method == 'POST':
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
        return redirect(url_for('admin.complete'))
    return render_template('confirm.html', form_data=session['form_data'])

@admin_bp.route('/complete')
def complete():
    return render_template('complete.html')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect('inquiries.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[0], password):
            session['logged_in'] = True
            session['username'] = username
            flash('ログイン成功！', 'success')
            return redirect(url_for('admin.db_show'))
        else:
            flash('ユーザー名またはパスワードが間違っています。', 'danger')
    return render_template('login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/database')
def db_show():
    if not session.get('logged_in'):
        flash('このページを表示するにはログインが必要です。', 'warning')
        return redirect(url_for('admin.login'))
    conn = sqlite3.connect('inquiries.db')
    c = conn.cursor()
    db_datas = [row for row in c.execute('SELECT * FROM inquiries')]
    conn.close()
    return render_template('database.html', db_datas=db_datas)

@admin_bp.route('/manage/<int:id>', methods=['GET', 'POST'])
def deleting_record(id):
    if not session.get('logged_in'):
        flash('このページを表示するにはログインが必要です。', 'warning')
        return redirect(url_for('admin.login'))
    conn = sqlite3.connect('inquiries.db')
    c = conn.cursor()
    db_data = list(c.execute('SELECT * FROM inquiries WHERE id = ?', (id,)))
    conn.close()
    if request.method == 'GET':
        if 'token' not in session:
            csrf_token = randomname(n)
            session['token'] = csrf_token
        else:
            csrf_token = session['token']
        return render_template('manage.html', db_data=db_data, csrf_token=csrf_token)
    elif request.method == 'POST':
        form_token = request.form.get('csrf_token')
        session_token = session.pop('token', None)
        if not form_token or form_token != session_token:
            abort(403)
        conn = sqlite3.connect('inquiries.db')
        c = conn.cursor()
        c.execute('DELETE FROM inquiries WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        flash(f'ID {id} を削除しました。', 'success')
        return redirect(url_for('admin.db_show'))

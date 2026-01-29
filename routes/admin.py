from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
import sqlite3
import random
from models.functions import randomname, n
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import os

admin_bp = Blueprint('admin', __name__)

UPLOAD_FOLDER = 'static/uploads/astro'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route("/admin")
def admin_index():
    if session.get('logged_in'):
        return redirect(url_for('admin.db_show'))
    return redirect(url_for('admin.login'))

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
        from database import get_db
        conn = get_db()
        cursor = conn.cursor()
        form_data = session['form_data']
        cursor.execute('''
            INSERT INTO inquiries (name, email, age, content)
            VALUES (?, ?, ?, ?)
        ''', (form_data['name'], form_data['email'] ,form_data['age'], form_data['content']))
        conn.commit()
        # conn.close()
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
        from database import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        # conn.close()
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
    from database import get_db
    conn = get_db()
    c = conn.cursor()
    db_datas = [row for row in c.execute('SELECT * FROM inquiries')]
    # conn.close()
    return render_template('database.html', db_datas=db_datas)

@admin_bp.route('/manage/<int:id>', methods=['GET', 'POST'])
def deleting_record(id):
    if not session.get('logged_in'):
        flash('このページを表示するにはログインが必要です。', 'warning')
        return redirect(url_for('admin.login'))
    from database import get_db
    conn = get_db()
    c = conn.cursor()
    db_data = list(c.execute('SELECT * FROM inquiries WHERE id = ?', (id,)))
    # conn.close()
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
        from database import get_db
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM inquiries WHERE id = ?', (id,))
        conn.commit()
        # conn.close()
        flash(f'ID {id} を削除しました。', 'success')
        return redirect(url_for('admin.db_show'))

# Astro Events Management
@admin_bp.route('/astro_events')
def astro_list():
    if not session.get('logged_in'):
        return redirect(url_for('admin.login'))
    
    from database import get_moon_db
    conn = get_moon_db()
    # conn.row_factory = sqlite3.Row # Already set
    c = conn.cursor()
    events = c.execute('SELECT * FROM astro_events ORDER BY iso_date').fetchall()
    # conn.close()
    
    # CSRF Token generation
    if 'token' not in session:
        session['token'] = randomname(n)
    
    return render_template('admin_astro_list.html', events=events, csrf_token=session['token'])

@admin_bp.route('/astro_events/add', methods=['GET', 'POST'])
def astro_add():
    if not session.get('logged_in'):
        return redirect(url_for('admin.login'))
        
    if request.method == 'POST':
        # Verify CSRF
        if request.form.get('csrf_token') != session.get('token'):
            abort(403)
            
        slug = request.form.get('slug')
        title = request.form.get('title')
        date_text = request.form.get('date_text')
        description = request.form.get('description')
        details = request.form.get('details')
        tips = request.form.get('tips')
        badge = request.form.get('badge')
        iso_date = request.form.get('iso_date')
        
        badge = request.form.get('badge')
        iso_date = request.form.get('iso_date')
        # Checkbox is 'on' if checked, None otherwise
        is_important = 1 if request.form.get('is_important') else 0
        
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # ファイル名の重複を避けるために一意性を確保するのが望ましいが、簡易的に
                filename = f"{slug}_{filename}"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                image_url = f"uploads/astro/{filename}"
        
        from database import get_moon_db
        conn = get_moon_db()
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO astro_events (slug, title, date_text, description, details, tips, badge, iso_date, image_url, is_important)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (slug, title, date_text, description, details, tips, badge, iso_date, image_url, is_important))
            conn.commit()
            flash('イベントを作成しました。', 'success')
            return redirect(url_for('admin.astro_list'))
        except sqlite3.IntegrityError:
            flash('エラー: スラッグが既に使用されています。別のスラッグを指定してください。', 'danger')
        finally:
            # conn.close()
            pass
            
    if 'token' not in session:
        session['token'] = randomname(n)
        
    return render_template('admin_astro_edit.html', event=None, csrf_token=session['token'])

@admin_bp.route('/astro_events/edit/<int:id>', methods=['GET', 'POST'])
def astro_edit(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin.login'))
        
    from database import get_moon_db
    conn = get_moon_db()
    # conn.row_factory = sqlite3.Row
    c = conn.cursor()
    event = c.execute('SELECT * FROM astro_events WHERE id = ?', (id,)).fetchone()
    
    if not event:
        # conn.close()
        flash('イベントが見つかりません。', 'warning')
        return redirect(url_for('admin.astro_list'))
        
    if request.method == 'POST':
        # Verify CSRF
        if request.form.get('csrf_token') != session.get('token'):
            # conn.close()
            abort(403)
            
        slug = request.form.get('slug')
        title = request.form.get('title')
        date_text = request.form.get('date_text')
        description = request.form.get('description')
        details = request.form.get('details')
        tips = request.form.get('tips')
        badge = request.form.get('badge')
        iso_date = request.form.get('iso_date')
        
        badge = request.form.get('badge')
        iso_date = request.form.get('iso_date')
        is_important = 1 if request.form.get('is_important') else 0
        
        image_url = event['image_url'] # デフォルトは既存のパス
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{slug}_{filename}"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                image_url = f"uploads/astro/{filename}"
        
        try:
            c.execute('''
                UPDATE astro_events 
                SET slug=?, title=?, date_text=?, description=?, details=?, tips=?, badge=?, iso_date=?, image_url=?, is_important=?
                WHERE id=?
            ''', (slug, title, date_text, description, details, tips, badge, iso_date, image_url, is_important, id))
            conn.commit()
            flash('イベントを更新しました。', 'success')
            # conn.close()
            return redirect(url_for('admin.astro_list'))
        except sqlite3.IntegrityError:
            flash('エラー: スラッグが既に使用されています。別のスラッグを指定してください。', 'danger')
            # conn.close()
            # リロードせずにフォーム再表示するならここでrender_templateすべきだが、簡易的にredirect
            return redirect(url_for('admin.astro_edit', id=id))

    # conn.close()
    if 'token' not in session:
        session['token'] = randomname(n)
        
    return render_template('admin_astro_edit.html', event=event, csrf_token=session['token'])

@admin_bp.route('/astro_events/delete/<int:id>', methods=['POST'])
def astro_delete(id):
    if not session.get('logged_in'):
        return redirect(url_for('admin.login'))
        
    if request.form.get('csrf_token') != session.get('token'):
        abort(403)
        
    from database import get_moon_db
    conn = get_moon_db()
    c = conn.cursor()
    c.execute('DELETE FROM astro_events WHERE id = ?', (id,))
    conn.commit()
    # conn.close()
    
    flash('イベントを削除しました。', 'success')
    return redirect(url_for('admin.astro_list'))

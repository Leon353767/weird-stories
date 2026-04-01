from flask import Flask, render_template, request, redirect, url_for, session, abort
from datetime import datetime
from markupsafe import escape
import secrets
import database
import os

app = Flask(__name__)

# ========== الإعدادات الأمنية ==========
app.secret_key = secrets.token_hex(32)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

ADMIN_PASSWORD = "las45ps29ij06vb54fg76"
login_attempts = {}

# قائمة الكلمات الممنوعة (موسعة)
FORBIDDEN_WORDS = [
    'sex', 'porn', 'xxx', 'drugs', 'hate', 'kill', 'terrorist', 'bomb', 
    'fuck', 'shit', 'asshole', 'nigger', 'faggot', 'bitch', 'cunt',
    'cock', 'dick', 'pussy', 'whore', 'slut', 'bastard', 'damn'
]

# ========== دوال مساعدة للأمان ==========
def contains_forbidden_words(text):
    """التحقق من وجود كلمات ممنوعة في النص"""
    if not text:
        return False
    text_lower = text.lower()
    for word in FORBIDDEN_WORDS:
        if word in text_lower:
            return True
    return False

def sanitize_text(text):
    """تنظيف النص من الأكواد الضارة"""
    if not text:
        return ''
    return escape(text)

# تهيئة قاعدة البيانات
database.init_db()

# ========== Routes ==========
@app.route('/')
def index():
    stories = database.get_all_stories()
    return render_template('index.html', stories=stories, session=session, request=request, current_category=None)

@app.route('/category/<category>')
def category(category):
    valid_categories = ['Funny', 'Scary', 'Weird']
    if category not in valid_categories:
        abort(404)
    stories = database.get_stories_by_category(category)
    return render_template('index.html', stories=stories, session=session, request=request, current_category=category)

@app.route('/add', methods=['GET', 'POST'])
def add_story():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category')
        password = request.form.get('password', '').strip()
        
        # التحقق من صحة الإدخالات
        if not title or not content or not password:
            return "<h2>❌ All fields are required!</h2><a href='/add'>Go back</a>", 400
        if len(title) > 200:
            return "<h2>❌ Title is too long (max 200 characters)!</h2><a href='/add'>Go back</a>", 400
        if len(content) > 5000:
            return "<h2>❌ Story is too long (max 5000 characters)!</h2><a href='/add'>Go back</a>", 400
        if len(password) < 3:
            return "<h2>❌ Password must be at least 3 characters!</h2><a href='/add'>Go back</a>", 400
        
        # التحقق من الكلمات الممنوعة
        if contains_forbidden_words(title):
            return "<h2>❌ Your story title contains inappropriate language!</h2><a href='/add'>Go back</a>", 400
        if contains_forbidden_words(content):
            return "<h2>❌ Your story contains inappropriate language!</h2><a href='/add'>Go back</a>", 400
        
        # تنظيف النصوص
        title = sanitize_text(title)
        content = sanitize_text(content)
        
        date = datetime.now().strftime("%Y-%m-%d")
        database.add_story(title, content, category, date, password)
        return redirect(url_for('index'))
    
    return render_template('add_story.html')

@app.route('/story/<int:story_id>', methods=['GET', 'POST'])
def story_detail(story_id):
    story = database.get_story(story_id)
    if not story:
        abort(404)
    
    if request.method == 'POST':
        comment_text = request.form.get('comment', '').strip()
        
        if not comment_text:
            return "<h2>❌ Comment cannot be empty!</h2><a href='/story/" + str(story_id) + "'>Go back</a>", 400
        if len(comment_text) > 1000:
            return "<h2>❌ Comment is too long (max 1000 characters)!</h2><a href='/story/" + str(story_id) + "'>Go back</a>", 400
        
        # التحقق من الكلمات الممنوعة في التعليق
        if contains_forbidden_words(comment_text):
            return "<h2>❌ Your comment contains inappropriate language!</h2><a href='/story/" + str(story_id) + "'>Go back</a>", 400
        
        # تنظيف النص
        comment_text = sanitize_text(comment_text)
        
        date = datetime.now().strftime("%Y-%m-%d")
        database.add_comment(story_id, comment_text, date)
        return redirect(url_for('story_detail', story_id=story_id))
    
    comments = database.get_comments(story_id)
    return render_template('story_detail.html', story=story, comments=comments)

@app.route('/delete_story/<int:story_id>', methods=['GET', 'POST'])
def delete_story(story_id):
    story = database.get_story(story_id)
    if not story:
        abort(404)
    
    if request.method == 'POST':
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'true'
        
        if is_admin:
            if password == ADMIN_PASSWORD:
                database.delete_story(story_id)
                return redirect(url_for('index'))
            else:
                return "<h2>❌ Wrong admin password!</h2><a href='/delete_story/" + str(story_id) + "'>Try again</a>", 403
        else:
            if database.check_story_password(story_id, password):
                database.delete_story(story_id)
                return redirect(url_for('index'))
            else:
                return "<h2>❌ Wrong story password!</h2><a href='/delete_story/" + str(story_id) + "'>Try again</a>", 403
    
    return render_template('delete_confirm.html', story=story)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    ip = request.remote_addr
    if ip in login_attempts and login_attempts[ip] >= 5:
        return "<h2>🚫 Too many failed attempts. Please try again later.</h2>", 403
    
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            login_attempts[ip] = 0
            session['admin'] = True
            return redirect(url_for('index'))
        else:
            login_attempts[ip] = login_attempts.get(ip, 0) + 1
            remaining = 5 - login_attempts[ip]
            return f"<h2>❌ Wrong admin password! {remaining} attempts remaining.</h2><a href='/admin_login'>Try again</a>", 403
    
    return render_template('admin_login.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# ========== رابط سري للمشرف ==========
ADMIN_SECRET_KEY = "kl98yh65df90"  # غير هذا الرمز إلى ما تريد

@app.route('/admin/<secret>')
def admin_panel(secret):
    if secret == ADMIN_SECRET_KEY:
        session['admin'] = True
        return redirect(url_for('index'))
    return "Page not found", 404

# ========== معالجة الأخطاء ==========
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidden(e):
    return "<h2>🚫 Access denied</h2>", 403

@app.errorhandler(413)
def too_large(e):
    return "<h2>📁 File too large. Maximum size is 5MB.</h2>", 413

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
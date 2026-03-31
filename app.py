from flask import Flask, render_template, request, redirect, url_for, session, abort
from datetime import datetime
from markupsafe import escape
import secrets
import database
import re
import os

app = Flask(__name__)

# ========== الإعدادات الأمنية ==========
# مفتاح سري قوي
app.secret_key = secrets.token_hex(32)

# تحديد الحجم الأقصى للمحتوى (5 ميغابايت)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# كلمة مرور المشرف (غيّرها إلى كلمة قوية)
ADMIN_PASSWORD = "las45ps29ij06vb54fg76"

# تتبع محاولات تسجيل الدخول الفاشلة
login_attempts = {}

# قائمة الكلمات الممنوعة (يمكنك توسيعها)
FORBIDDEN_WORDS = ['sex', 'porn', 'xxx', 'drugs', 'hate', 'kill', 'terrorist', 'bomb', 'fuck', 'shit', 'asshole']

# ========== دوال مساعدة للأمان ==========
def contains_forbidden_words(text):
    """التحقق من وجود كلمات ممنوعة في النص"""
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

def is_admin_ip(ip):
    """التحقق من عنوان IP الخاص بالمشرف (اختياري)"""
    admin_ips = ['127.0.0.1', '::1']
    return ip in admin_ips

# تهيئة قاعدة البيانات
database.init_db()

# ========== Routes ==========
@app.route('/')
def index():
    stories = database.get_all_stories()
    return render_template('index.html', stories=stories, session=session, request=request, current_category=None)

@app.route('/category/<category>')
def category(category):
    # التحقق من صحة الفئة
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
            return "❌ All fields are required!", 400
        
        if len(title) > 200:
            return "❌ Title is too long (max 200 characters)!", 400
        
        if len(content) > 5000:
            return "❌ Story is too long (max 5000 characters)!", 400
        
        if len(password) < 3:
            return "❌ Password must be at least 3 characters!", 400
        
        # التحقق من الكلمات الممنوعة
        if contains_forbidden_words(title) or contains_forbidden_words(content):
            return "❌ Your story contains inappropriate content!", 400
        
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
            return "❌ Comment cannot be empty!", 400
        
        if len(comment_text) > 1000:
            return "❌ Comment is too long (max 1000 characters)!", 400
        
        # التحقق من الكلمات الممنوعة
        if contains_forbidden_words(comment_text):
            return "❌ Your comment contains inappropriate content!", 400
        
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
                return "❌ Wrong admin password! <a href='/delete_story/" + str(story_id) + "'>Try again</a>", 403
        else:
            if database.check_story_password(story_id, password):
                database.delete_story(story_id)
                return redirect(url_for('index'))
            else:
                return "❌ Wrong story password! <a href='/delete_story/" + str(story_id) + "'>Try again</a>", 403
    
    return render_template('delete_confirm.html', story=story)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    ip = request.remote_addr
    
    # التحقق من عدد محاولات الدخول الفاشلة
    if ip in login_attempts and login_attempts[ip] >= 5:
        return "🚫 Too many failed attempts. Please try again later.", 403
    
    if request.method == 'POST':
        password = request.form.get('password')
        
        if password == ADMIN_PASSWORD:
            login_attempts[ip] = 0
            session['admin'] = True
            session.permanent = True
            return redirect(url_for('index'))
        else:
            login_attempts[ip] = login_attempts.get(ip, 0) + 1
            remaining = 5 - login_attempts[ip]
            return f"❌ Wrong admin password! {remaining} attempts remaining.", 403
    
    return render_template('admin_login.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# ========== معالجة الأخطاء ==========
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return "🚫 Access denied", 403

@app.errorhandler(413)
def too_large(e):
    return "📁 File too large. Maximum size is 5MB.", 413

# ========== تشغيل التطبيق ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
import sqlite3

DB_PATH = 'stories.db'

def init_db():
    """تهيئة قاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT NOT NULL, 
                  content TEXT NOT NULL, 
                  category TEXT NOT NULL, 
                  date TEXT NOT NULL, 
                  password TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  story_id INTEGER NOT NULL, 
                  comment_text TEXT NOT NULL, 
                  date TEXT NOT NULL)''')
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

def add_story(title, content, category, date, password):
    """إضافة قصة جديدة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO stories (title, content, category, date, password) VALUES (?,?,?,?,?)",
              (title, content, category, date, password))
    conn.commit()
    conn.close()

def get_all_stories():
    """جلب جميع القصص"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM stories ORDER BY id DESC")
    stories = c.fetchall()
    conn.close()
    return stories

def get_stories_by_category(category):
    """جلب القصص حسب الفئة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM stories WHERE category = ? ORDER BY id DESC", (category,))
    stories = c.fetchall()
    conn.close()
    return stories

def add_comment(story_id, comment_text, date):
    """إضافة تعليق"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO comments (story_id, comment_text, date) VALUES (?,?,?)",
              (story_id, comment_text, date))
    conn.commit()
    conn.close()

def get_comments(story_id):
    """جلب تعليقات قصة معينة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM comments WHERE story_id = ? ORDER BY id DESC", (story_id,))
    comments = c.fetchall()
    conn.close()
    return comments

def get_story(story_id):
    """جلب قصة معينة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
    story = c.fetchone()
    conn.close()
    return story

def delete_story(story_id):
    """حذف قصة وجميع تعليقاتها"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM stories WHERE id = ?", (story_id,))
    c.execute("DELETE FROM comments WHERE story_id = ?", (story_id,))
    conn.commit()
    conn.close()

def check_story_password(story_id, password):
    """التحقق من كلمة مرور القصة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password FROM stories WHERE id = ?", (story_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == password
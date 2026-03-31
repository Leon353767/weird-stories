import sqlite3

def init_db():
    conn = sqlite3.connect('stories.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stories
                 (id INTEGER PRIMARY KEY, title TEXT, content TEXT, category TEXT, date TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id INTEGER PRIMARY KEY, story_id INTEGER, comment_text TEXT, date TEXT)''')
    conn.commit()
    conn.close()

def add_story(title, content, category, date, password):
    conn = sqlite3.connect('stories.db')
    c = conn.cursor()
    c.execute("INSERT INTO stories (title, content, category, date, password) VALUES (?,?,?,?,?)",
              (title, content, category, date, password))
    conn.commit()
    conn.close()

def get_all_stories():
    conn = sqlite3.connect('stories.db')
    c = conn.cursor()
    c.execute("SELECT * FROM stories ORDER BY id DESC")
    stories = c.fetchall()
    conn.close()
    return stories

def get_stories_by_category(category):
    conn = sqlite3.connect('stories.db')
    c = conn.cursor()
    c.execute("SELECT * FROM stories WHERE category = ? ORDER BY id DESC", (category,))
    stories = c.fetchall()
    conn.close()
    return stories

def add_comment(story_id, comment_text, date):
    conn = sqlite3.connect('stories.db')
    c = conn.cursor()
    c.execute("INSERT INTO comments (story_id, comment_text, date) VALUES (?,?,?)",
              (story_id, comment_text, date))
    conn.commit()
    conn.close()

def get_comments(story_id):
    conn = sqlite3.connect('stories.db')
    c = conn.cursor()
    c.execute("SELECT * FROM comments WHERE story_id = ? ORDER BY id DESC", (story_id,))
    comments = c.fetchall()
    conn.close()
    return comments

def get_story(story_id):
    conn = sqlite3.connect('stories.db')
    c = conn.cursor()
    c.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
    story = c.fetchone()
    conn.close()
    return story

def delete_story(story_id):
    conn = sqlite3.connect('stories.db')
    c = conn.cursor()
    c.execute("DELETE FROM stories WHERE id = ?", (story_id,))
    c.execute("DELETE FROM comments WHERE story_id = ?", (story_id,))
    conn.commit()
    conn.close()

def check_story_password(story_id, password):
    conn = sqlite3.connect('stories.db')
    c = conn.cursor()
    c.execute("SELECT password FROM stories WHERE id = ?", (story_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0] == password
    return False
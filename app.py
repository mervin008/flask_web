import os
from flask import Flask, render_template, request, g, redirect, url_for
import markdown
import mistune
from datetime import datetime
import libsql_experimental as libsql

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_strong_secret_key')

# Turso database configuration (from environment variables)
app.config['TURSO_DB_URL'] = os.environ.get('TURSO_DB_URL')
app.config['TURSO_AUTH_TOKEN'] = os.environ.get('TURSO_AUTH_TOKEN')

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_db():
    if 'db' not in g:
        g.db = libsql.connect(
            database=app.config['TURSO_DB_URL'],
            auth_token=app.config['TURSO_AUTH_TOKEN']
        )
    return g.db


def get_posts():
    db = get_db()

    cursor = db.execute("PRAGMA table_info(posts)")
    columns = [row[1] for row in cursor.fetchall()]  # Extract column names

    rows = db.execute('SELECT * FROM posts ORDER BY created_at ASC').fetchall()
    posts = [dict(zip(columns, row)) for row in rows] 
    return posts

def get_post(post_id):
    db = get_db()

    cursor = db.execute("PRAGMA table_info(posts)")
    columns = [row[1] for row in cursor.fetchall()] 

    row = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if row:
        return dict(zip(columns, row)) 
    return None

@app.route('/post/<int:post_id>')
def show_post(post_id):
    post = get_post(post_id)
    if post:
        post['content'] = mistune.markdown(post['content'])

        db = get_db()
        prev_post_id = db.execute('SELECT id FROM posts WHERE id < ? ORDER BY id DESC LIMIT 1', (post_id,)).fetchone()
        next_post_id = db.execute('SELECT id FROM posts WHERE id > ? ORDER BY id ASC LIMIT 1', (post_id,)).fetchone()

        return render_template('post.html', post=post, post_id=post_id,
                               prev_post_id=prev_post_id[0] if prev_post_id else None,
                               next_post_id=next_post_id[0] if next_post_id else None)
    else:
        return 'Post not found', 404

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        short_desc = request.form['short_desc']
        content = request.form['content']

        db = get_db()
        db.execute(
            'INSERT INTO posts (title, short_desc, content) VALUES (?, ?, ?)',
            (title, short_desc, content)
        )
        db.commit()

        return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = get_post(post_id)

    if post:
        if request.method == 'POST':
            title = request.form['title']
            short_desc = request.form['short_desc']
            content = request.form['content']

            db = get_db()
            db.execute(
                'UPDATE posts SET title = ?, short_desc = ?, content = ? WHERE id = ?',
                (title, short_desc, content, post_id)
            )
            db.commit()

            return redirect(url_for('show_post', post_id=post_id))
        else:
            return render_template('edit.html', post=post)
    else:
        return 'Post not found', 404

@app.context_processor  
def inject_year():
    return dict(year=datetime.now().year) 

@app.route('/')
def index():
    posts = get_posts()
    return render_template('index.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True)
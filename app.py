import os
from flask import Flask, render_template, request, g, redirect, url_for
import markdown
import mistune
import mysql.connector

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_strong_secret_key')

# Database configuration (from environment variables)
app.config['DATABASE_HOST'] = os.environ.get('DATABASE_HOST')
app.config['DATABASE_NAME'] = os.environ.get('DATABASE_NAME')
app.config['DATABASE_USER'] = os.environ.get('DATABASE_USER')
app.config['DATABASE_PASSWORD'] = os.environ.get('DATABASE_PASSWORD')

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=app.config['DATABASE_HOST'],
            database=app.config['DATABASE_NAME'],
            user=app.config['DATABASE_USER'],
            password=app.config['DATABASE_PASSWORD']
        )
    return g.db


def get_posts():
    db = get_db()
    cursor = db.cursor(dictionary=True)  # Use dictionary=True
    cursor.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = cursor.fetchall()
    return posts

def get_post(post_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)  # Use dictionary=True
    cursor.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()
    return post

@app.route('/')
def index():
    posts = get_posts()
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>')
def show_post(post_id):
    post = get_post(post_id)
    if post:
        post['content'] = mistune.markdown(post['content'])
        return render_template('post.html', post=post, post_id=post_id)
    else:
        return 'Post not found', 404

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        short_desc = request.form['short_desc']
        content = request.form['content']

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO posts (title, short_desc, content) VALUES (%s, %s, %s)',
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
            cursor = db.cursor()
            cursor.execute(
                'UPDATE posts SET title = %s, short_desc = %s, content = %s WHERE id = %s',
                (title, short_desc, content, post_id)
            )
            db.commit()

            return redirect(url_for('show_post', post_id=post_id))
        else:
            return render_template('edit.html', post=post)
    else:
        return 'Post not found', 404

if __name__ == '__main__':
    app.run(debug=True)
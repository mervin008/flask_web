import os
from flask import Flask, render_template, request, g, redirect, url_for, flash
from db import get_db, init_db, close_db
import markdown
import mistune

app = Flask(__name__)
app.config['DATABASE'] = os.path.join(app.root_path, 'blog.db')
app.config['SECRET_KEY'] = 'your_secret_key'

# Import db module, not individual functions
import db

# Initialize database and register close_db
db.init_app(app)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_posts():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = cursor.fetchall()
    return posts

def get_post(post_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
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
        post = dict(post)
        post['content'] = mistune.markdown(post['content'])
        return render_template('post.html', post=post,  post_id=post_id)
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
        post = dict(post)
        if request.method == 'POST':
            post['title'] = request.form['title']
            post['short_desc'] = request.form['short_desc']
            post['content'] = request.form['content']

            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                'UPDATE posts SET title = ?, short_desc = ?, content = ? WHERE id = ?',
                (post['title'], post['short_desc'], post['content'], post_id)
            )
            db.commit()

            flash('Post updated successfully!', 'success')  # Add a flash message
            return redirect(url_for('show_post', post_id=post_id))  # Redirect to the post
        return render_template('edit.html', post=post)
    else:
        return 'Post not found', 404


if __name__ == '__main__':
    app.run(debug=True)
import os
from flask import Flask, render_template, request, g, redirect, url_for
import markdown
import mistune
from datetime import datetime
import libsql_experimental as libsql
from slugify import slugify  
from collections import defaultdict

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_strong_secret_key')

# Turso database configuration 
app.config['TURSO_DB2_URL'] = os.environ.get('TURSO_DB2_URL')
app.config['TURSO_AUTH2_TOKEN'] = os.environ.get('TURSO_AUTH2_TOKEN')

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_db():
    if 'db' not in g:
        g.db = libsql.connect(
            database=app.config['TURSO_DB2_URL'],
            auth_token=app.config['TURSO_AUTH2_TOKEN']
        )
    return g.db

def get_posts():
    db = get_db()

    cursor = db.execute("PRAGMA table_info(postslug)")  # Changed table name
    columns = [row[1] for row in cursor.fetchall()]

    rows = db.execute('SELECT * FROM postslug ORDER BY created_at ASC').fetchall()  # Changed table name
    posts = [dict(zip(columns, row)) for row in rows] 
    return posts

def get_post_by_slug(slug):  # Define the function
    db = get_db()
    cursor = db.execute("PRAGMA table_info(postslug)")  
    columns = [row[1] for row in cursor.fetchall()] 

    row = db.execute('SELECT * FROM postslug WHERE slug = ?', (slug,)).fetchone()
    if row:
        return dict(zip(columns, row)) 
    return None

@app.route('/post/<string:post_slug>')
def show_post(post_slug):
    post = get_post_by_slug(post_slug)
    if post:
        post['content'] = mistune.markdown(post['content'])

        db = get_db()
        cursor = db.cursor()

        # Previous Post Logic
        cursor.execute('SELECT title FROM postslug WHERE created_at < ? ORDER BY created_at DESC LIMIT 1', (post['created_at'],))
        prev_post_title = cursor.fetchone()
        prev_post_slug = slugify(prev_post_title[0]) if prev_post_title else None

        # Next Post Logic (remains the same)
        cursor.execute('SELECT title FROM postslug WHERE created_at > ? ORDER BY created_at ASC LIMIT 1', (post['created_at'],))
        next_post_title = cursor.fetchone()
        next_post_slug = slugify(next_post_title[0]) if next_post_title else None

        return render_template('post.html', post=post, post_slug=post_slug,
                               prev_post_slug=prev_post_slug, next_post_slug=next_post_slug)
    else:
        return 'Post not found', 404

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        slug = slugify(title) 
        short_desc = request.form['short_desc']
        content = request.form['content']
        tags = request.form['tags'].split(',') 
        tags = [tag.strip().capitalize() for tag in tags if tag.strip()] 

        db = get_db()
        db.execute(
            'INSERT INTO postslug (title, slug, short_desc, content, tags) VALUES (?, ?, ?, ?, ?)',
            (title, slug, short_desc, content, ','.join(tags)) 
        )
        db.commit()

        return redirect(url_for('show_post', post_slug=slug)) 
    return render_template('create.html')

@app.route('/edit/<string:post_slug>', methods=['GET', 'POST'])
def edit_post(post_slug):
    post = get_post_by_slug(post_slug)
    if post:
        if request.method == 'POST':
            title = request.form['title']
            slug = slugify(title) 
            short_desc = request.form['short_desc']
            content = request.form['content']
            tags = request.form['tags'].split(',')
            tags = [tag.strip().capitalize() for tag in tags if tag.strip()] 

            db = get_db()
            db.execute(
                'UPDATE postslug SET title = ?, slug = ?, short_desc = ?, content = ?, tags = ? WHERE id = ?',
                (title, slug, short_desc, content, ','.join(tags), post['id']) 
            )
            db.commit()

            return redirect(url_for('show_post', post_slug=slug)) 
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
    all_tags = set()
    
    for post in posts:
        tags = post['tags'].split(',')
        for tag in tags:
            if tag.strip():
                all_tags.add(tag.strip())

    # Get all unique tags grouped by category
    grouped_tags = defaultdict(set)
    for post in posts:
        tags = post['tags'].split(',')
        for tag in tags:
            tag = tag.strip()
            if tag:
                if tag[0].isalpha():
                    category = tag[0].upper()
                else:
                    category = "Others"
                grouped_tags[category].add(tag)

    # Sort tags alphabetically within each category and all tags
    for category, tags in grouped_tags.items():
        grouped_tags[category] = sorted(tags)
    all_tags = sorted(all_tags)  # Sort all_tags alphabetically

    return render_template('index.html', posts=posts, grouped_tags=grouped_tags, all_tags=all_tags)
if __name__ == '__main__':
    app.run(debug=True)
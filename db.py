import sqlite3
from flask import Flask, g, current_app
from flask.cli import with_appcontext

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_app(app: Flask):
    app.teardown_appcontext(close_db)

    # Create a Flask CLI command for initializing the database
    @app.cli.command('init-db')
    @with_appcontext
    def init_db_command():
        """Clear the existing data and create new tables."""
        init_db()
        print('Initialized the database.')
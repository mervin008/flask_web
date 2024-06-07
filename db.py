import mysql.connector
from flask import g, current_app

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=current_app.config['DATABASE_HOST'],
            database=current_app.config['DATABASE_NAME'],
            user=current_app.config['DATABASE_USER'],
            password=current_app.config['DATABASE_PASSWORD']
        )
    return g.db
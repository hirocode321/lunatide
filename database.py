import sqlite3
from flask import g

DATABASE = 'inquiries.db'
MOON_DATABASE = 'moon_data.db'

def get_db(db_name=DATABASE):
    db_attr = f'_database_{db_name.replace(".", "_")}'
    db = getattr(g, db_attr, None)
    if db is None:
        db = sqlite3.connect(db_name)
        db.row_factory = sqlite3.Row
        setattr(g, db_attr, db)
    return db

def get_moon_db():
    return get_db(MOON_DATABASE)

def close_connection(exception):
    """Closes all database connections stored in flask.g."""
    for attr in list(g.__dict__.keys()):
        if attr.startswith('_database_'):
            db = getattr(g, attr)
            if db is not None:
                db.close()

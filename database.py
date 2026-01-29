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
    # Close inquiries.db
    db_attr = f'_database_{DATABASE.replace(".", "_")}'
    db = getattr(g, db_attr, None)
    if db is not None:
        db.close()
    
    # Close moon_data.db
    db_attr_moon = f'_database_{MOON_DATABASE.replace(".", "_")}'
    db_moon = getattr(g, db_attr_moon, None)
    if db_moon is not None:
        db_moon.close()

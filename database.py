import sqlite3
from flask import g

def connect_to_database():
    sql = sqlite3.connect('database.db')
    sql.row_factory = sqlite3.Row
    return sql


def get_database():
    if not hasattr(g, 'crud_db'):
        g.crud_db = connect_to_database()
    return g.crud_db
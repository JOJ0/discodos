#import discogs_client
#import csv
import time
import sqlite3
from sqlite3 import Error
import datetime

def create_conn(file):
    try:
        conn = sqlite3.connect(file)
        return conn
    except Error as e:
        log.error("DB connection error: %s", e)
    return None

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        log.error("%s", e)

def create_release(conn, release):
    #sql  = "INSERT INTO releases(discogs_id, discogs_title)"
    #sql += "    VALUES("+str(r.release.id)+", '"+str(r.release.title)+"')"
    sql  = '''INSERT INTO releases(discogs_id, discogs_title, update_date)
                    VALUES('?', '?')'''
    cur = conn.cursor()
    cur.execute('''INSERT INTO releases(discogs_id, discogs_title) VALUES(?, ?)''', (release.release.id, release.release.title))
    log.info("cur.rowcount: %s", e)
    return cur.lastrowid

def all_releases(conn):
    cur = conn.cursor()
    cur.execute('''SELECT * FROM releases''')
    rows = cur.fetchall()
    for row in rows:
        log.info("%s", row)

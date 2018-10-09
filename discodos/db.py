import time
import sqlite3
from sqlite3 import Error
import datetime
from discodos import log, db

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
        log.debug("Executed sql: %s", create_table_sql)
    except Error as e:
        log.error("%s", e)

def create_release(conn, release):
    #sql  = "INSERT INTO releases(discogs_id, discogs_title)"
    #sql += "    VALUES("+str(r.release.id)+", '"+str(r.release.title)+"')"
    #sql  = '''INSERT INTO releases(discogs_id, discogs_title, update_date)
    #                VALUES('?', '?')'''
    cur = conn.cursor()
    cur.execute('''INSERT INTO releases(discogs_id, discogs_title) VALUES(?, ?)''', (release.release.id, release.release.title))
    log.info("cur.rowcount: %s", e)
    return cur.lastrowid

def all_releases(conn):
    cur = conn.cursor()
    cur.execute('''SELECT * FROM releases''')
    rows = cur.fetchall()
    return rows
    #for row in rows:
    #    print(str(row[0])+'\t\t'+row[1], row[2])

def search_release_id(conn, discogs_id):
    log.debug('DB search for Discogs Release ID: %s\n', discogs_id)
    cur = conn.cursor()
    cur.execute('''SELECT * FROM releases WHERE discogs_id == ?;''', [str(discogs_id)])
    rows = cur.fetchall()
    return rows

def search_release_title(conn, discogs_title):
    log.debug('DB search for Discogs Release Title: %s\n', discogs_title)
    cur = conn.cursor()
    cur.execute("SELECT * FROM releases WHERE discogs_title LIKE ?", ("%"+discogs_title+"%", ), )
    rows = cur.fetchall()
    return rows

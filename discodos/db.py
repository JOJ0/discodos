#import discogs_client
#import csv
import time
import sqlite3
from sqlite3 import Error
import datetime

def create_conn(file):
    try:
        conn = sqlite3.connect(file)
        print(sqlite3.version)
        return conn
    except Error as e:
        print(e)
    return None

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def create_release(conn, release):
    #sql  = "INSERT INTO releases(discogs_id, discogs_title)"
    #sql += "    VALUES("+str(r.release.id)+", '"+str(r.release.title)+"')"
    sql  = '''INSERT INTO releases(discogs_id, discogs_title, update_date)
                    VALUES('?', '?')'''
    cur = conn.cursor()
    cur.execute('''INSERT INTO releases(discogs_id, discogs_title) VALUES(?, ?)''', (release.release.id, release.release.title))
    print("INFO: cur.rowcount: "+str(cur.rowcount))
    return cur.lastrowid

def all_releases(conn):
    cur = conn.cursor()
    cur.execute('''SELECT * FROM releases''')
    rows = cur.fetchall()
    for row in rows:
        print(row)

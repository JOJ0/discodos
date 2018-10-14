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
    log.info("cur.rowcount: %s\n", cur.rowcount)
    return cur.lastrowid

def all_releases(conn):
    cur = conn.cursor()
    cur.execute('''SELECT * FROM releases''')
    rows = cur.fetchall()
    return rows

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

def add_track_to_mix(conn, mix_id, release_id, track_no, track_pos=0,
                     track_key='', track_key_notes=''):
    cur = conn.cursor()
    cur.execute('''INSERT INTO mix_track (mix_id, d_release_id,
                       track_no, track_pos, track_key, track_key_notes)
                       VALUES(?, ?, ?, ?, ?, ?)''',
                       (mix_id, release_id, track_no, track_pos,
                        track_key, track_key_notes))
    log.info("cur.rowcount: %s", cur.rowcount)
    return cur.lastrowid

def add_new_mix(conn, name, played='', venue=''):
    cur = conn.cursor()
    cur.execute('''INSERT INTO mix (name, created, updated, played, venue)
                       VALUES (?, datetime('now', 'localtime'), '', ?, ?)''',
                       (name, played, venue))
    log.info("cur.rowcount: %s", cur.rowcount)
    return cur.lastrowid

def get_mix_id(conn, mix_id):
    cur = conn.cursor()
    cur.execute('''SELECT mix_id FROM mix WHERE mix_id == ?''', (mix_id, ))
    rows = cur.fetchone()
    return rows

def get_last_track_in_mix(conn, mix_id):
    cur = conn.cursor()
    cur.execute('''SELECT MAX(track_pos) FROM mix_track WHERE mix_id == ?''', (mix_id, ))
    row = cur.fetchone()
    #log.debug('DB get_last_track_in_mix: %s\n', row)
    return row

def get_full_mix(conn, mix_id):
    cur = conn.cursor()
    log.debug('DB getting mix table by ID: %s\n', mix_id)
    cur.execute('''SELECT track_pos, discogs_title, track_no, track_key,
                          track_key_notes
                       FROM mix_track INNER JOIN mix
                           ON mix.mix_id = mix_track.mix_id INNER JOIN releases
                           ON mix_track.d_release_id = releases.discogs_id
                       WHERE mix_track.mix_id == ?''', (mix_id, ))
    rows = cur.fetchall()
    if len(rows) == 0:
        log.debug('DB nothing found')
        return False
    else:
        return rows


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
        log.error("DB: Connection error: %s", e)
    return None

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        log.info("DB: Executed sql: %s", create_table_sql)
    except Error as e:
        log.error("%s", e)

def create_release(conn, release):
    cur = conn.cursor()
    cur.execute('''INSERT INTO release(discogs_id, discogs_title, import_timestamp) VALUES(?, ?, datetime('now', 'localtime'))''', (release.release.id, release.release.title))
    log.info("cur.rowcount: %s\n", cur.rowcount)
    return cur.lastrowid

def create_track(conn, track_id, release_id, track_no, track_name):
    cur = conn.cursor()
    cur.execute('''INSERT INTO track(track_id, d_release_id, d_track_no,
                                     d_track_name, import_timestamp)
                       VALUES(?, ?, ?, ?, datetime('now', 'localtime'))''',
                       (track_id, release_id, track_no, track_name))
    log.info("cur.rowcount: %s\n", cur.rowcount)
    return cur.lastrowid

def all_releases(conn):
    cur = conn.cursor()
    cur.execute('''SELECT * FROM release''')
    rows = cur.fetchall()
    return rows

def search_release_id(conn, discogs_id):
    log.debug('DB: Search for Discogs Release ID: %s\n', discogs_id)
    cur = conn.cursor()
    cur.execute('''SELECT * FROM release WHERE discogs_id == ?;''', [str(discogs_id)])
    rows = cur.fetchall()
    return rows

def search_release_title(conn, discogs_title):
    log.debug('DB: Search for Discogs Release Title: %s\n', discogs_title)
    cur = conn.cursor()
    cur.execute("SELECT * FROM release WHERE discogs_title LIKE ?", ("%"+discogs_title+"%", ), )
    rows = cur.fetchall()
    return rows

def add_track_to_mix(conn, mix_id, release_id, track_no, track_pos=0,
                     track_key='', track_key_notes=''):
    cur = conn.cursor()
    cur.execute('''INSERT INTO mix_track (mix_id, d_release_id, track_no, track_pos,
                       trans_rating, trans_notes)
                       VALUES(?, ?, ?, ?, ?, ?)''',
                       (mix_id, release_id, track_no, track_pos,
                        trans_rating, trans_notes))
    log.info("DB: cur.rowcount: %s", cur.rowcount)
    return cur.lastrowid

def add_new_mix(conn, name, played='', venue=''):
    cur = conn.cursor()
    cur.execute('''INSERT INTO mix (name, created, updated, played, venue)
                       VALUES (?, datetime('now', 'localtime'), '', date(?), ?)''',
                       (name, played, venue))
    log.info("cur.rowcount: %s", cur.rowcount)
    return cur.lastrowid

def get_mix_info(conn, mix_id):
    cur = conn.cursor()
    cur.execute('''SELECT * FROM mix WHERE mix_id == ?''', (mix_id, ))
    rows = cur.fetchone()
    return rows

def get_last_track_in_mix(conn, mix_id):
    cur = conn.cursor()
    cur.execute('''SELECT MAX(track_pos) FROM mix_track WHERE mix_id == ?''', (mix_id, ))
    row = cur.fetchone()
    log.info('DB: get_last_track_in_mix: %s\n', row)
    return row

def get_full_mix(conn, mix_id):
    cur = conn.cursor()
    log.debug('DB getting mix table by ID: %s\n', mix_id)
    cur.execute('''SELECT track_pos, discogs_title, track_no, track_key,
                          track_key_notes
                       FROM mix_track INNER JOIN mix
                           ON mix.mix_id = mix_track.mix_id INNER JOIN release
                           ON mix_track.d_release_id = release.discogs_id
                       WHERE mix_track.mix_id == ?''', (mix_id, ))
    rows = cur.fetchall()
    if len(rows) == 0:
        log.info('DB nothing found')
        return False
    else:
        return rows

def get_all_mixes(conn):
    cur = conn.cursor()
    log.info('DB: Getting mixes table')
    cur.execute('''SELECT * FROM mix''')
    rows = cur.fetchall()
    return rows

def get_mix_id(conn, mixname):
    cur = conn.cursor()
    log.info('DB: Getting mix_id via mix name "%s". Only returns first match',
                 mixname)
    cur.execute('''SELECT mix_id FROM mix WHERE name LIKE ?''', ("%"+mixname+"%", ))
    rows = cur.fetchone()
    if rows:
        return rows
    else:
        log.info("DB: Can't fetch mix ID by name")
        return False

def mix_id_existing(conn, mix_id):
    cur = conn.cursor()
    log.info('DB: Checking if mix_id is existing')
    cur.execute('''SELECT mix_id FROM mix WHERE mix_id == ?''', (mix_id, ))
    rows = cur.fetchone()
    if rows:
        return rows
    else:
        return rows


def get_tracks_in_mixes(conn):
    cur = conn.cursor()
    log.info('DB: Getting all tracks from mix_track table')
    cur.execute('''SELECT * FROM mix_track''')
    rows = cur.fetchall()
    return rows

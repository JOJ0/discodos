import time
import sqlite3
from sqlite3 import Error
import datetime
from discodos import log, db, utils
from discodos.utils import *

# BASIC DB HANDLING
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
        log.error("DB: %s", e)


# RELEASE / TRACK INFO FROM DISCOGS
def create_release(conn, release_id, release_title):
    cur = conn.cursor()
    #if collection_item == True:
    cur.execute('''INSERT INTO release(discogs_id, discogs_title, import_timestamp)
                       VALUES(?, ?, datetime('now', 'localtime'))''',
                       (release_id, release_title))
    #else:
    #    cur.execute('''INSERT INTO release(discogs_id, discogs_title, import_timestamp)
    #                       VALUES(?, ?, datetime('now', 'localtime'))''',
    #                       (release.id, release.title))
    log.info("cur.rowcount: %s\n", cur.rowcount)
    return cur.lastrowid

def all_releases(conn):
    cur = conn.cursor()
    cur.execute('''SELECT * FROM release ORDER BY discogs_title''')
    rows = cur.fetchall()
    return rows

def search_release_id(conn, discogs_id):
    log.info('DB: Search for Discogs Release ID: %s\n', discogs_id)
    cur = conn.cursor()
    cur.execute('''SELECT * FROM release WHERE discogs_id == ?;''', [str(discogs_id)])
    rows = cur.fetchall()
    return rows

def search_release_title(conn, discogs_title):
    log.debug('DB: Search for Discogs Release Title: %s\n', discogs_title)
    cur = conn.cursor()
    cur.execute("SELECT * FROM release WHERE discogs_title LIKE ?", ("%"+discogs_title+"%", ), )
    rows = cur.fetchall()
    log.debug('DB: search_release_title returns: %s', rows)
    return rows

def create_track(conn, release_id, track_no, track_title):
    with conn:
        cur = conn.cursor()
        cur.execute('''INSERT INTO track(d_release_id, d_track_no,
                                         d_track_name, import_timestamp)
                           VALUES(?, ?, ?, datetime('now', 'localtime'))''',
                           (release_id, track_no, track_title))
        log.info("DB: cur.rowcount: %s\n", cur.rowcount)
    return cur.lastrowid


# MIXES
def add_new_mix(conn, name, played='', venue=''):
    log.debug("DB: add_new_mix got: {}, {}, {}.".format(name, played, venue))
    cur = conn.cursor()
    cur.execute('''INSERT INTO mix (name, created, updated, played, venue)
                       VALUES (?, datetime('now', 'localtime'), '', date(?), ?)''',
                       (name, played, venue))
    log.info("DB: cur.rowcount: %s", cur.rowcount)
    return cur.lastrowid

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

def get_mix_info(conn, mix_id):
    cur = conn.cursor()
    log.info('DB: Getting general info about mix %s', mix_id)
    cur.execute('''SELECT * FROM mix WHERE mix_id == ?''', (mix_id, ))
    rows = cur.fetchone()
    return rows

def delete_mix(conn, _mix_id):
    cur = conn.cursor()
    log.info('DB: Deleting mix %s and all its mix_track entries (through cascade)', _mix_id)
    cur.execute('''DELETE FROM mix WHERE mix_id == ?''', (_mix_id, ))
    log.info("DB: cur.rowcount: %s", cur.rowcount)
    return cur.lastrowid


# TRACKS IN MIXES
def get_last_track_in_mix(conn, mix_id):
    cur = conn.cursor()
    cur.execute('''SELECT MAX(track_pos) FROM mix_track WHERE mix_id == ?''', (mix_id, ))
    row = cur.fetchone()
    log.info('DB: get_last_track_in_mix: %s\n', row)
    return row

def get_full_mix(conn, mix_id, detail="coarse"):
    cur = conn.cursor()
    log.info('DB getting mix table by ID: %s\n', mix_id)
    if detail == "coarse":
        cur.execute('''SELECT track_pos, discogs_title, mix_track.d_track_no,
                               trans_rating, key, bpm
                           FROM
                             mix_track
                                 INNER JOIN mix
                                 ON mix.mix_id = mix_track.mix_id
                                   INNER JOIN release
                                   ON mix_track.d_release_id = release.discogs_id
                                     LEFT OUTER JOIN track
                                     ON mix_track.d_release_id = track.d_release_id
                                     AND mix_track.d_track_no = track.d_track_no
                                       LEFT OUTER JOIN track_ext
                                       ON mix_track.d_release_id = track_ext.d_release_id
                                       AND mix_track.d_track_no = track_ext.d_track_no
                           WHERE mix_track.mix_id == ?
                           ORDER BY mix_track.track_pos''', (mix_id, ))
    else:
        cur.execute('''SELECT track_pos, discogs_title, d_track_name,
                               mix_track.d_track_no,
                               key, bpm, key_notes, trans_rating, trans_notes, notes
                           FROM
                             mix_track
                                 INNER JOIN mix
                                 ON mix.mix_id = mix_track.mix_id
                                   INNER JOIN release
                                   ON mix_track.d_release_id = release.discogs_id
                                     LEFT OUTER JOIN track
                                     ON mix_track.d_release_id = track.d_release_id
                                     AND mix_track.d_track_no = track.d_track_no
                                       LEFT OUTER JOIN track_ext
                                       ON mix_track.d_release_id = track_ext.d_release_id
                                       AND mix_track.d_track_no = track_ext.d_track_no
                           WHERE mix_track.mix_id == ?
                           ORDER BY mix_track.track_pos''', (mix_id, ))
    rows = cur.fetchall()
    if len(rows) == 0:
        log.info('DB nothing found')
        return False
    else:
        return rows

def get_all_tracks_in_mixes(conn):
    cur = conn.cursor()
    log.info('DB: Getting all tracks from mix_track table')
    cur.execute('''SELECT * FROM mix_track''')
    rows = cur.fetchall()
    return rows

def get_tracks_of_one_mix(conn, _mix_id):
    cur = conn.cursor()
    log.info('DB: Getting tracks of mix %s\n', _mix_id)
    cur.execute('''SELECT * FROM mix_track WHERE mix_id == ?''', (_mix_id, ))
    rows = cur.fetchall()
    return rows

def add_track_to_mix(conn, mix_id, release_id, track_no, track_pos=0,
                     trans_rating='', trans_notes=''):
    log.debug("DB: add_track_to_mix got this: mix_id: {}, d_release_id: {}, track_no: {}, track_pos: {}, trans_rating: {}, trans_notes: {}".format(mix_id, release_id, track_no, track_pos, trans_rating, trans_notes))
    cur = conn.cursor()
    cur.execute('''INSERT INTO mix_track (mix_id, d_release_id, d_track_no, track_pos,
                       trans_rating, trans_notes)
                       VALUES(?, ?, ?, ?, ?, ?)''',
                       (mix_id, release_id, track_no, track_pos,
                        trans_rating, trans_notes))
    log.info("DB: cur.rowcount: %s", cur.rowcount)
    conn.commit()
    return cur.lastrowid
    #return cur.rowcount

def get_one_mix_track(conn, mix_id, position):
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    log.debug('DB getting details of a mix-track by ID %s and position %s\n',
               mix_id, position)
    cur.execute('''SELECT track_pos, discogs_title, d_track_name, mix_track.d_track_no,
                          trans_rating, trans_notes, key, key_notes, bpm, notes,
                          mix_track_id, mix_track.d_release_id
                       FROM
                         mix_track
                             INNER JOIN mix
                             ON mix.mix_id = mix_track.mix_id
                               INNER JOIN release
                               ON mix_track.d_release_id = release.discogs_id
                                 LEFT OUTER JOIN track
                                 ON mix_track.d_release_id = track.d_release_id
                                 AND mix_track.d_track_no = track.d_track_no
                                   LEFT OUTER JOIN track_ext
                                   ON mix_track.d_release_id = track_ext.d_release_id
                                   AND mix_track.d_track_no = track_ext.d_track_no
                       WHERE mix_track.mix_id == ?
                         AND mix_track.track_pos == ?''', (mix_id, position))
    rows = cur.fetchone()
    return rows

# first part of track in mix update
def update_track_in_mix(conn, mix_track_id, _release_id, track_no,
                        track_pos_new, trans_rating, trans_notes,):
    with conn:
        cur = conn.cursor()
        log.info("DB: update_track_in_mix mix_track_id: %s", str(mix_track_id))
        log.info("DB: update_track_in_mix release_id: %s", str(_release_id))
        log.info("DB: update_track_in_mix track_no: %s", track_no)
        cur.execute('''UPDATE mix_track SET d_release_id = ?, d_track_no = ?, track_pos = ?,
                           trans_rating = ?, trans_notes = ?
                           WHERE mix_track_id == ?
                           ''',
                           (_release_id, track_no, track_pos_new,
                            trans_rating, trans_notes, mix_track_id))
        log.info("DB: update_track_in_mix rowcount: %s", cur.rowcount)
        return cur.lastrowid

# second part of track in mix update
def update_or_insert_track_ext(conn, release_id_orig, release_id_new, track_no,
                        key, key_notes, bpm, notes):
    with conn:
        cur = conn.cursor()
        cur.execute('''UPDATE track_ext SET d_release_id= ?, key = ?, key_notes = ?,
                           bpm = ?, notes = ?
                           WHERE d_release_id == ?
                           AND d_track_no == ?
                           ''',
                           (release_id_new, key, key_notes,
                            bpm, notes, release_id_new, track_no))
        log.info("DB: update track_ext rowcount: %s", cur.rowcount)
        # if 0 rows -> was not found (actually same as select), do insert
        log.info("release_id_orig: %s", release_id_orig)
        log.info("release_id_new: %s", release_id_new)
        if cur.rowcount == 0:
            self.execute_sql('''INSERT INTO track_ext (key, key_notes, bpm, notes,
                                                  d_release_id, d_track_no)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                           (key, key_notes, bpm, notes,
                            release_id_new, track_no))
            log.info("DB: insert track_ext rowcount: %s", cur.rowcount)
        #return cur.lastrowid

def get_tracks_from_position(conn, _mix_id, _pos):
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('''SELECT mix_track_id, track_pos FROM mix_track WHERE mix_id == ?
                       AND track_pos >= ? ''', (_mix_id, _pos))
    rows = cur.fetchall()
    log.debug('DB: get_tracks_from_position: %s\n', rows)
    if len(rows) == 0:
        log.info('DB: get_tracks_from_position: Nothing found')
        return False
    else:
        return rows

def update_pos_in_mix(conn, mix_track_id, track_pos_new):
    log.info("DB: update_pos_in_mix: track_pos_new is {}".format(track_pos_new))
    cur = conn.cursor()
    try:
        cur.execute('''UPDATE mix_track SET track_pos = ?
                           WHERE mix_track_id == ?
                           ''',
                           (track_pos_new,
                            mix_track_id))
        conn.commit()
        log.info("DB: update_pos_in_mix rowcount: %s", cur.rowcount)
        return True
    except sqlite3.Error as er:
        log.error("DB: update_pos_in_mix error: %s", er.message)
        return False


def delete_track_from_mix(conn, _mix_id, _pos):
    cur = conn.cursor()
    log.info('DB: Deleting track %i from mix %i', _pos, int(_mix_id))
    del_successful = cur.execute('''DELETE FROM mix_track WHERE mix_id == ?
                                        AND track_pos ==?''', (_mix_id, _pos))
    log.info('DB: DELETE successful? %i', del_successful.rowcount)
    if del_successful.rowcount:
        return True
    else:
        return False

def get_mix_tracks_to_copy(conn, _mix_id):
    cur = conn.cursor()
    log.info('DB: Getting tracks for mix ID %s', _mix_id)
    cur.execute('''SELECT d_release_id, d_track_no, track_pos, trans_rating, trans_notes
                       FROM mix_track WHERE mix_id == ?''',(_mix_id, ))
    rows = cur.fetchall()
    return rows


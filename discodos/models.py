from discodos.utils import * # most of this should only be in view
from abc import ABC, abstractmethod
from discodos import log
from tabulate import tabulate as tab # should only be in view
import pprint
import discogs_client
import discogs_client.exceptions as errors
import requests.exceptions as reqerrors
import urllib3.exceptions as urlerrors
from sqlite3 import Error as sqlerr
import sqlite3
import time
from datetime import datetime

class Database (object):

    def __init__(self, db_conn=False, db_file=False):
        if db_conn:
            log.debug("DB-NEW: db_conn argument was handed over.")
            self.db_conn = db_conn
        else:
            log.debug("DB-NEW: Creating connection to db_file.")
            if not db_file:
                log.debug("DB-NEW: No db_file given, using default name.")
                db_file = './discobase.db'
            self.db_conn = self.create_conn(db_file)
            
        self.db_conn.row_factory = sqlite3.Row # also this was in each db.function before
        self.cur = self.db_conn.cursor() # we had this in each db function before
        self.configure_db() # set PRAGMA options

    def create_conn(self, db_file):
        try:
            conn = sqlite3.connect(str(db_file)) # make sure it's a string
            return conn
        except sqlerr as e:
            log.error("DB-NEW: Connection error: %s", e)
        return None

    def execute_sql(self, sql, values_tuple = False, raise_err = False):
        '''used for eg. creating tables or inserts'''
        log.info("DB-NEW: execute_sql: %s", sql)
        try:
            with self.db_conn: # auto commits and auto rolls back on exceptions
                c = self.cur  # connection close has to be done manually though!
                if values_tuple:
                    c.execute(sql, values_tuple)
                    log.info("DB-NEW: ...with this tuple: {%s}", values_tuple)
                else:
                    c.execute(sql)
                log.info("DB-NEW: rowcount: {}, lastrowid: {}".format(c.rowcount,
                    c.lastrowid))
                #log.info("DB-NEW: Committing NOW")
                #self.db_conn.commit()
            log.info("DB-NEW: Committing via context close NOW")
            self.lastrowid = c.lastrowid
            return c.rowcount
        except sqlerr as e:
            #log.error("DB-NEW: %s", dir(e))
            if raise_err:
                log.info("DB-NEW: Raising error to upper level.")
                raise e
            else:
                log.error("DB-NEW: %s", e.args[0])
            return False

    def configure_db(self):
        settings = "PRAGMA foreign_keys = ON;"
        self.execute_sql(settings)

    def _select_simple(self, fields_list, table, condition = False, fetchone = False, orderby = False):
        """This is a wrapper around the _select method.
           It puts together sql select statements as strings.
        """
        log.info("DB-NEW: _select_simple: fetchone = {}".format(fetchone))
        fields_str = ""
        for cnt,field in enumerate(fields_list):
            if cnt == 0:
                fields_str += field
            else:
                fields_str += ", {}".format(field)
        if condition:
            where_or_not = "WHERE {}".format(condition)
        else:
            where_or_not = ""
        if orderby:
            orderby_or_not = "ORDER BY {}".format(orderby)
        else:
            orderby_or_not = ""
        select_str = "SELECT {} FROM {} {} {};".format(fields_str, table, where_or_not, orderby_or_not)
        return self._select(select_str, fetchone)

    def _select(self, sql_select, fetchone = False):
        """Executes sql selects in two possible ways: fetchone or fetchall
           It's completely string based and not aware of tuple based
           values substitution in sqlite3 cursor objects.

        @param sql_select (string): the complete sql select statement
        @param fetchone (bool): defaults to False (return multiple rows)
        @return (type is depending on running mode)
            fetchone = True:
                something found: sqlite3.Row (dict-like) object
                nothing found: None
            fetchone = False (fetchall, this is the default)
                something found: a list of sqlite3.Row (dict-like) objects
                nothing found: an empty list
        """
        log.info("DB-NEW: _select: {}".format(sql_select))
        self.cur.execute(sql_select)
        if fetchone:
            rows = self.cur.fetchone()
        else:
            rows = self.cur.fetchall()

        if rows:
            log.debug("DB-NEW: rowcount: {}, lastrowid: {} (irrelevant in selects)".format(
                self.cur.rowcount, self.cur.lastrowid))
            if fetchone: # len will return column count
                log.info('DB-NEW: Found 1 row containing {} columns.'.format(len(rows.keys())))
            else: # len will return rows count
                log.info('DB-NEW: Found {} rows containing {} columns.'.format(
                    len(rows), len(rows[0])))
            log.debug("DB-NEW: Returning row(s) as type: {}.".format(type(rows).__name__))
            return rows
        else:
            log.info('DB-NEW: Nothing found - Returning type: {}.'.format(type(rows).__name__))
            return rows # was empty list before, now it's either empty list or NoneType

    def close_conn(self): # manually close conn! - context manager (with) doesn't do it
        self.db_conn.close()

# mix model class
class Mix (Database):

    def __init__(self, db_conn, mix_name_or_id, db_file = False):
        super(Mix, self).__init__(db_conn, db_file)
        # figuring out names and IDs, just logs and sets instance attributes, no exits here! 
        self.name_or_id = mix_name_or_id
        self.id_existing = False
        self.name_existing = False
        self.info = []
        self.name = False
        self.created = False
        self.updated = False
        self.played = False
        self.venue = False
        if is_number(mix_name_or_id):
            self.id = mix_name_or_id
            # if it's a mix-id, get mix-name and info
            try:
                self.info = self.get_mix_info()
                # FIXME info should also be available as single attrs: created, venue, etc.
                self.name = self.info[1]
                self.id_existing = True
                self.name_existing = True
            except:
                log.info("Mix ID is not existing yet!")
                #raise Exception # use this for debugging
                #raise SystemExit(1)
        else:
            self.name = mix_name_or_id
            # if it's a mix-name, get the id unless it's "all"
            # (default value, should only show mix list)
            if not self.name == "all":
                try:
                    mix_id_tuple = self._get_mix_id(self.name)
                    log.debug('MODEL: mix_id_tuple type: %s', type(mix_id_tuple).__name__)
                    self.id = mix_id_tuple[0]
                    self.id_existing = True
                    self.name_existing = True
                    # load basic mix-info from DB
                    # FIXME info should also be available as single attrs: created, venue, etc.
                    # FIXME or okay? here we assume mix is existing and id could be fetched
                    try:
                        self.info = self.get_mix_info()
                        self.name = self.info[1]
                    except:
                        log.info("Can't get mix info.")
                        #raise Exception # use this for debugging
                except:
                    log.info("Can't get mix-name from id. Mix not existing yet?")
                    #raise Exception # use this for debugging
                    #raise SystemExit(1)
        if self.id_existing:
            self.created = self.info[2]
            self.played = self.info[4]
            self.venue = self.info[5]
        log.debug("MODEL: Mix info is {}.".format(self.info))
        log.debug("MODEL: Name is {}.".format(self.name))
        log.debug("MODEL: Played is {}.".format(self.played))
        log.debug("MODEL: Venue is {}.".format(self.venue))

    # fixme mix info should probably be properties to keep them current
    #@property
    #def.name(self):
    #    return db.get_mix_info(self.db_conn, self.id)[1]

    def _get_mix_id(self, mixname): # this method should only be called from __init__
        #return self._select_simple(["mix_id"], 'mix', fetchone = True,
        #    condition = 'name LIKE "%{}%"'.format(mix_name))
        log.info('MODEL: Getting mix_id via mix name "%s". Only returns first match',
                     mixname)
        if is_number(mixname):
            log.info("MODEL: mix name is a number, won't try to fetch from DB")
            return mixname # we were probably been given an ID already, return it.
        else:
            self.cur.execute(
                'SELECT mix_id FROM mix WHERE name LIKE ?', ("%{}%".format(mixname), ))
            row = self.cur.fetchone()
            if row:
                log.info("MODEL: Found mix ID: {}".format(row["mix_id"]))
                return row
            else:
                log.info("MODEL: Can't fetch mix ID by name")
                return row

    def delete(self):
        log.info('MODEL: Deleting mix %s and all its mix_track entries (through cascade)',
            self.id)
        del_return = self.execute_sql('DELETE FROM mix WHERE mix_id == ?', (self.id, ))
        log.info("MODEL: Deleted mix, DB returned: {}".format(del_return))
        self.id_existing = False
        self.name_existing = False # as soon as it's deleted, name is available again
        self.info = []
        # self.name = False # keep name so we still know after delete
        self.created = False
        self.updated = False
        self.played = False
        self.venue = False
        return del_return

    def create(self, _played, _venue, new_mix_name = False):
        log.info("MODEL: Creating new mix.")
        if not new_mix_name:
            new_mix_name = self.name
        sql_create = '''INSERT INTO mix (name, created, updated, played, venue)
                       VALUES (?, datetime('now', 'localtime'), '', date(?), ?)'''
        values = (new_mix_name, _played, _venue)
        db_rowcount = self.execute_sql(sql_create, values)
        log.info("MODEL: New mix created with ID {}.".format(self.lastrowid))
        self.id_existing = True
        self.name_existing = True
        self.id = self.lastrowid
        self.info = self.get_mix_info()
        self.name = self.info[1]
        self.created = self.info[2]
        self.updated = self.info[3]
        self.played = self.info[4]
        self.venue = self.info[5]
        return db_rowcount

    def get_all_mixes(self):
        """
        get metadata of all mixes from db

        @param
        @return sqlite fetchall rows object
        @author
        """
        # we want to select * but in a different order:
        log.info("MODEL: Getting mixes table.")
        mixes_data = self._select_simple(['mix_id', 'name', 'played', 'venue', 'created', 'updated'],
                'mix', condition=False, orderby='played')
        return mixes_data

    def get_one_mix_track(self, track_id):
        log.info("MODEL: Returning track {} from mix {}.".format(track_id, self.id))
        _where = 'mix_track.mix_id == {} AND mix_track.track_pos == {}'.format(self.id,
            track_id)
        _join = '''mix_track INNER JOIN mix
                                ON mix.mix_id = mix_track.mix_id
                                  INNER JOIN release
                                  ON mix_track.d_release_id = release.discogs_id
                                    LEFT OUTER JOIN track
                                    ON mix_track.d_release_id = track.d_release_id
                                    AND mix_track.d_track_no = track.d_track_no
                                      LEFT OUTER JOIN track_ext
                                      ON mix_track.d_release_id = track_ext.d_release_id
                                      AND mix_track.d_track_no = track_ext.d_track_no'''
        return self._select_simple(['track_pos', 'discogs_title', 'd_track_name',
            'mix_track.d_track_no', 'trans_rating', 'trans_notes', 'key', 'key_notes',
             'bpm', 'notes', 'mix_track_id', 'mix_track.d_release_id'],
             _join, fetchone = True, condition = _where)

    def update_mix_track_and_track_ext(self, track_details, edit_answers):
        log.info("MODEL: Updating track in mix_track and track_ext tables.")
        log.debug("MODEL: track_details dict: {}".format(track_details))
        log.debug("MODEL: edit_answers dict: {}".format(edit_answers))
        mix_track_cols=['d_release_id', 'd_track_no', 'track_pos', 'trans_rating', 'trans_notes']
        track_ext_cols=['key', 'bpm', 'key_notes', 'notes']
        values_mix_track = '' # mix_track update
        values_list_mix_track = []
        values_track_ext = '' # track_ext update
        values_list_track_ext = []
        cols_insert_track_ext = '' # track_ext insert
        values_insert_track_ext = '' # (the tuple is the same obviously)
        if 'track_pos' in edit_answers: #filter out track_pos='not a number'
            if edit_answers['track_pos'] == 'not a number':
                edit_answers.pop('track_pos')
        mix_track_edit = False # decide if it's table mix_track or track_ext
        track_ext_edit = False
        for key in edit_answers:
            if key in mix_track_cols:
                mix_track_edit = True
            if key in track_ext_cols:
                track_ext_edit = True

        if mix_track_edit:
            update_mix_track = 'UPDATE mix_track SET '
            where_mix_track = 'WHERE mix_track_id == {}'.format(track_details['mix_track_id'])
            for cnt,answer in enumerate(edit_answers.items()):
                log.debug('key: {}, value: {}'.format(answer[0], answer[1]))
                if answer[0] in mix_track_cols:
                    if values_mix_track == '':
                        values_mix_track += "{} = ? ".format(answer[0], answer[1])
                    else:
                        values_mix_track += ", {} = ? ".format(answer[0], answer[1])
                    values_list_mix_track.append(answer[1])
            final_update_mix_track = update_mix_track + values_mix_track + where_mix_track
            #log.info('MODEL: {}'.format(final_update_mix_track))
            #log.info(log.info('MODEL: {}'.format(tuple(values_list_mix_track))))
            with self.db_conn:
                log.info("MODEL: Now really executing mix_track update...")
                self.execute_sql(final_update_mix_track, tuple(values_list_mix_track))

        if track_ext_edit:
            update_track_ext = 'UPDATE track_ext SET '
            insert_track_ext = 'INSERT INTO track_ext'
            where_track_ext = 'WHERE d_release_id == {} AND d_track_no == \"{}\"'.format(
                                track_details['d_release_id'], track_details['d_track_no'])
            for cnt,answer in enumerate(edit_answers.items()):
                log.debug('key: {}, value: {}'.format(answer[0], answer[1]))
                if answer[0] in track_ext_cols:
                    if values_track_ext == '':
                        values_track_ext += "{} = ? ".format(answer[0], answer[1])
                    else:
                        values_track_ext += ", {} = ? ".format(answer[0], answer[1])
                    values_list_track_ext.append(answer[1])

                    if values_insert_track_ext == '':
                        cols_insert_track_ext += "{}".format(answer[0])
                        values_insert_track_ext += "?".format(answer[1])
                    else:
                        cols_insert_track_ext += ", {}".format(answer[0])
                        values_insert_track_ext += ", ?".format(answer[1])
                    # the list is the same as with update

            final_update_track_ext = update_track_ext + values_track_ext + where_track_ext
            final_insert_track_ext = "{} ({}, d_release_id, d_track_no) VALUES ({}, ?, ?)".format(
                    insert_track_ext, cols_insert_track_ext, values_insert_track_ext)

            #log.info('MODEL: {}'.format(final_update_track_ext))
            #log.info('MODEL: {}'.format(tuple(values_list_track_ext)))

            #log.info('MODEL: {}'.format(final_insert_track_ext))
            values_insert_list_track_ext = values_list_track_ext[:]
            values_insert_list_track_ext.append(track_details['d_release_id'])
            values_insert_list_track_ext.append(track_details['d_track_no'])
            #log.info('MODEL: {}'.format(tuple(values_insert_list_track_ext)))

            with self.db_conn:
                log.info("MODEL: Now really executing track_ext update/insert...")
                #log.info(values_list_track_ext)
                #log.info(tuple(values_list_track_ext))

                dbret = self.execute_sql(final_update_track_ext, tuple(values_list_track_ext))
                if dbret == 0: # checks rowcount
                    log.info("MODEL: UPDATE didn't change anything, trying INSERT...")
                    dbret = self.execute_sql(final_insert_track_ext,
                        tuple(values_insert_list_track_ext))
            return dbret
        return False

    def get_tracks_from_position(self, pos):
        log.info('MODEL: Getting tracks in mix, starting at position {}.'.format(pos))
        #return db.get_tracks_from_position(self.db_conn, self.id, pos)
        return self._select_simple(['mix_track_id', 'track_pos'], 'mix_track',
            condition = "mix_id = {} AND track_pos >= {}".format(self.id, pos))

    def reorder_tracks(self, pos):
        log.info("MODEL: Reordering tracks in mix, starting at pos {}".format(pos))
        #tracks_to_shift = db.get_tracks_from_position(self.db_conn, self.id, pos)
        tracks_to_shift = self.get_tracks_from_position(pos)
        if not tracks_to_shift:
            return False
        for t in tracks_to_shift:
            log.info("MODEL: Shifting mix_track_id %i from pos %i to %i", t['mix_track_id'],
                     t['track_pos'], pos)
            sql_upd = 'UPDATE mix_track SET track_pos = ? WHERE mix_track_id == ?'
            ids_tuple = (pos, t['mix_track_id'])
            #if not db.update_pos_in_mix(self.db_conn, t['mix_track_id'], pos):
            #    return False
            if not self.execute_sql(sql_upd, ids_tuple):
                return False
            pos = pos + 1
        return True

    def reorder_tracks_squeeze_in(self, pos, tracks_to_shift):
        log.info('MODEL: Reordering because a track was squeezed in at pos {}.'.format(pos))
        if not tracks_to_shift:
            return False
        for t in tracks_to_shift:
            new_pos = t['track_pos'] + 1
            log.info("MODEL: Shifting mix_track_id %i from pos %i to %i", t['mix_track_id'],
                     t['track_pos'], new_pos)
            #if not db.update_pos_in_mix(self.db_conn, t['mix_track_id'], new_pos):
            #    return False
            sql_upd = 'UPDATE mix_track SET track_pos = ? WHERE mix_track_id == ?'
            ids_tuple = (new_pos, t['mix_track_id'])
            if not self.execute_sql(sql_upd, ids_tuple):
                return False
        return True

    def delete_track(self, pos):
        log.info("MODEL: Deleting track {} from {}.".format(pos, self.id))
        sql_del = 'DELETE FROM mix_track WHERE mix_id == ? AND track_pos == ?'
        ids_tuple = (self.id, pos)
        return self.execute_sql(sql_del, (ids_tuple))

    def get_full_mix(self, verbose = False):
        log.info('MODEL: Getting full mix.')
        if verbose:
            sql_sel = '''SELECT track_pos, discogs_title, track.d_artist, d_track_name,
                               mix_track.d_track_no,
                               key, bpm, key_notes, trans_rating, trans_notes, notes FROM'''
        else:
            sql_sel = '''SELECT track_pos, discogs_title, mix_track.d_track_no,
                               trans_rating, key, bpm FROM'''
        sql_sel+=''' 
                           mix_track INNER JOIN mix
                             ON mix.mix_id = mix_track.mix_id
                               INNER JOIN release
                               ON mix_track.d_release_id = release.discogs_id
                                 LEFT OUTER JOIN track
                                 ON mix_track.d_release_id = track.d_release_id
                                 AND mix_track.d_track_no = track.d_track_no
                                   LEFT OUTER JOIN track_ext
                                   ON mix_track.d_release_id = track_ext.d_release_id
                                   AND mix_track.d_track_no = track_ext.d_track_no
                       WHERE mix_track.mix_id == {}
                       ORDER BY mix_track.track_pos'''.format(self.id)
        return self._select(sql_sel, fetchone = False)

    def add_track(self, release_id, track_no, track_pos, trans_rating='', trans_notes=''):
        log.info('MODEL: Adding track to current mix.')
        log.debug("MODEL: add_track got this: mix_id: {}, d_release_id: {}, track_no: {}, track_pos: {}, trans_rating: {}, trans_notes: {}".format(
            self.id, release_id, track_no, track_pos, trans_rating, trans_notes))
        sql_add = '''INSERT INTO mix_track
            (mix_id, d_release_id, d_track_no, track_pos, trans_rating, trans_notes)
            VALUES(?, ?, ?, ?, ?, ?)'''
        values = (self.id, release_id, track_no, track_pos, trans_rating, trans_notes)
        return self.execute_sql(sql_add, values) # returns rowcount

    def get_last_track(self):
        log.info('MODEL: Getting last track in current mix')
        return self._select_simple(['MAX(track_pos)'], 'mix_track',
            condition = "mix_id = {}".format(self.id), fetchone = True)

    def get_tracks_of_one_mix(self, start_pos = False):
        log.info("MODEL: Getting tracks of a mix.")
        if not start_pos:
            where = "mix_id == {}".format(self.id)
        else:
            where = "mix_id == {} and track_pos >= {}".format(self.id, start_pos)
        return self._select_simple(['*'], 'mix_track', where,
                fetchone = False, orderby = 'track_pos')

    def get_all_tracks_in_mixes(self):
        log.info('MODEL: Getting all tracks from mix_track table.')
        return self._select_simple(['*'], 'mix_track', fetchone = False)

    def get_mix_info(self):
        log.info("MODEL: Getting mix info.")
        """
        get metadata of ONE mix from db

        @param
        @return sqlite fetchone rows object
        @author
        """
        mix_info = self._select_simple(['*'], 'mix', "mix_id == {}".format(self.id), fetchone = True)
        return mix_info

# record collection class
class Collection (Database):

    def __init__(self, db_conn, db_file = False):
        super(Collection, self).__init__(db_conn, db_file)
        # discogs api objects are online set when discogs_connect method is called
        self.d = False
        self.me = False
        self.ONLINE = False

    # discogs connect try,except wrapper, sets attributes d and me
    # leave globals for compatibility for now
    def discogs_connect(self, _userToken, _appIdentifier):
        try:
            self.d = discogs_client.Client(
                    _appIdentifier,
                    user_token = _userToken)
            self.me = self.d.identity()
            global d
            d = self.d
            global me
            me = self.me
            _ONLINE = True
        except Exception as Exc:
            _ONLINE = False
            #raise Exc
        self.ONLINE = _ONLINE
        return _ONLINE

    def get_all_db_releases(self):
        #return db.all_releases(self.db_conn)
        return self._select_simple(['discogs_id', 'd_artist', 'discogs_title',
            #'import_timestamp', 'in_d_collection'], 'release', orderby='d_artist, discogs_title')
            ], 'release', orderby='d_artist, discogs_title')

    def search_release_online(self, id_or_title):
        try:
            if is_number(id_or_title):
                release = self.d.release(id_or_title)
                #return '|'+str(release.id)+'|'+ str(release.title)+'|'
                return [release]
            else:
                releases = self.d.search(id_or_title, type='release')
                log.info("First found release: {}".format(releases[0]))
                log.debug("All found releases: {}".format(releases))
                return releases
        except errors.HTTPError as HtErr:
            log.error("%s", HtErr)
            return False
        except urlerrors.NewConnectionError as ConnErr:
            log.error("%s", ConnErr)
            return False
        except urlerrors.MaxRetryError as RetryErr:
            log.error("%s", RetryErr)
            return False
        except Exception as Exc:
            log.error("Exception: %s", Exc)
            return False

    def search_release_offline(self, id_or_title):
        if is_number(id_or_title):
            try:
                return self.search_release_id(id_or_title)
                if release:
                    return [release]
                else:
                    release_not_found = None
                    return release_not_found
            except Exception as Exc:
                log.error("Not found or Database Exception: %s\n", Exc)
                raise Exc
        else:
            try:
                releases = self._select_simple(['*'], 'release',
                        'discogs_title LIKE "%{}%" OR d_artist LIKE "%{}%"'.format(
                        id_or_title, id_or_title), fetchone = False, orderby = 'd_artist')
                if releases:
                    log.debug("First found release: {}".format(releases[0]))
                    log.debug("All found releases: {}".format(releases))
                    return releases # this is a list
                else:
                    return None
            except Exception as Exc:
                log.error("Not found or Database Exception: %s\n", Exc)
                raise Exc

    def create_track(self, release_id, track_no, track_name, track_artist):
        insert_tuple = (release_id, track_artist, track_no, track_name)
        update_tuple = (release_id, track_artist, track_no, track_name, release_id, track_no)
        c = self.db_conn.cursor()
        with self.db_conn:
            try:
                c.execute('''INSERT INTO track(d_release_id, d_artist, d_track_no,
                                                             d_track_name, import_timestamp)
                                               VALUES(?, ?, ?, ?, datetime('now', 'localtime'))''',
                                        insert_tuple)
                return c.rowcount
            except sqlerr as e:
                if "UNIQUE constraint failed" in e.args[0]:
                    log.warning("Track details already in DiscoBASE, updating ...")
                    try:
                        c.execute('''UPDATE track SET (d_release_id, d_artist, d_track_no,
                                                       d_track_name, import_timestamp)
                                       = (?, ?, ?, ?, datetime('now', 'localtime'))
                                          WHERE d_release_id == ? AND d_track_no == ?''', update_tuple)
                        log.info("MODEL: rowcount: %d, lastrowid: %d", c.rowcount, c.lastrowid)
                        return c.rowcount
                    except sqlerr as e:
                        log.error("MODEL: %s", e.args[0])
                        return False
                else:
                    log.error("MODEL: %s", e.args[0])
                    return False

    def search_release_id(self, release_id):
        #return db.search_release_id(self.db_conn, release_id)
        return self._select_simple(['*'], 'release',
            'discogs_id == {}'.format(release_id), fetchone = True)

    def create_release(self, release_id, release_title, release_artists, d_coll = False):
        try:
            insert_sql = '''INSERT OR FAIL INTO release(discogs_id, discogs_title,
                                    import_timestamp, d_artist, in_d_collection)
                                    VALUES(?, ?, ?, ?, ?)'''
            in_tuple = (release_id, release_title, datetime.today().isoformat(' ', 'seconds'),
                    release_artists, d_coll)
            rowcnt = self.execute_sql(insert_sql, in_tuple, raise_err = True)
            log.info("MODEL: rowcount: %d", rowcnt)
            return rowcnt
        except sqlerr as e:
            if "UNIQUE constraint failed" in e.args[0]:
                log.warning("Release already in DiscoBASE, updating ...")
                try:
                    upd_sql = '''UPDATE release SET (discogs_title,
                        import_timestamp, d_artist, in_d_collection)
                        = (?, ?, ?, ?) WHERE discogs_id == ?;'''
                    upd_tuple = (release_title, datetime.today().isoformat(' ', 'seconds'),
                        release_artists, d_coll, release_id)
                    rowcnt = self.execute_sql(upd_sql, upd_tuple, raise_err = True)
                    log.info("MODEL: rowcount: %d", rowcnt)
                    return rowcnt
                except sqlerr as e:
                    log.error("MODEL: %s", e.args[0])
                    return False
            else:
                log.error("MODEL: %s", e.args[0])
                return False

    def get_d_release(self, release_id):
        try:
            r = self.d.release(release_id)
            log.debug("try to access r here to catch err {}".format(r.title))
            return r
        except errors.HTTPError as HtErr:
            log.error('Release not existing on Discogs ({})'.format(HtErr))
            #log.error("%s", HtErr)
            return False
        except urlerrors.NewConnectionError as ConnErr:
            log.error("%s", ConnErr)
            return False
        except urlerrors.MaxRetryError as RetryErr:
            log.error("%s", RetryErr)
            return False
        except Exception as Exc:
            log.error("Exception: %s", Exc)
            #raise Exc
            return False

    def is_in_d_coll(self, release_id):
        successful = False
        for r in self.me.collection_folders[0].releases:
            #self.rate_limit_slow_downer(d, remaining=5, sleep=2)
            if r.release.id == release_id:
                #log.info(dir(r.release))
                return r
        return False
        #if not successful:
        #    return False

    def rate_limit_slow_downer(self, remaining=10, sleep=2):
        '''Discogs util: stay in 60/min rate limit'''
        if int(self.d._fetcher.rate_limit_remaining) < remaining:
            log.info("Discogs request rate limit is about to exceed,\
                      let's wait a bit: %s\n",
                         self.d._fetcher.rate_limit_remaining)
            #while int(self.d._fetcher.rate_limit_remaining) < remaining:
            time.sleep(sleep)
        else:
            log.info("Discogs rate limit info: %s remaining.", self.d._fetcher.rate_limit_remaining)

    def track_report_snippet(self, track_pos, mix_id):
        track_pos_before = track_pos - 1
        track_pos_after = track_pos + 1
        sql_sel = '''SELECT track_pos, discogs_title, track.d_artist, d_track_name,
                           mix_track.d_track_no,
                           key, bpm, key_notes, trans_rating, trans_notes, notes FROM'''
        sql_sel+='''
                           mix_track INNER JOIN mix
                             ON mix.mix_id = mix_track.mix_id
                               INNER JOIN release
                               ON mix_track.d_release_id = release.discogs_id
                                 LEFT OUTER JOIN track
                                 ON mix_track.d_release_id = track.d_release_id
                                 AND mix_track.d_track_no = track.d_track_no
                                   LEFT OUTER JOIN track_ext
                                   ON mix_track.d_release_id = track_ext.d_release_id
                                   AND mix_track.d_track_no = track_ext.d_track_no
                       WHERE (mix_track.track_pos == "{}" OR mix_track.track_pos == "{}"
                             OR mix_track.track_pos == "{}") AND mix_track.mix_id == "{}"
                       ORDER BY mix_track.track_pos'''.format(
                               track_pos, track_pos_before, track_pos_after, mix_id)
        tracks_snippet = self._select(sql_sel, fetchone = False)
        if not tracks_snippet:
            return False
        else:
            log.info("MODEL: Returning track_report_snippet data.")
            #self.cli.print_help(tracks_snippet)
            return tracks_snippet

    def track_report_occurences(self, release_id, track_no):
        occurences_data = self._select_simple(
                ['track_pos', 'mix_track.mix_id', 'mix.name'],
                 'mix_track INNER JOIN MIX ON mix.mix_id = mix_track.mix_id',
                 'd_release_id == "{}" AND d_track_no == "{}"'.format(release_id, track_no))
        log.info("MODEL: Returning track_report_occurences data.")
        return occurences_data

    def d_artists_to_str(self, d_artists):
        '''gets a combined string from discogs artistlist object'''
        artist_str=''
        for cnt,artist in enumerate(d_artists):
            if cnt == 0:
                artist_str = artist.name
            else:
                artist_str += ' / {}'.format(artist.name)
        log.info('MODEL: combined artistlist to string \"{}\"'.format(artist_str))
        return artist_str

    def d_artists_parse(self, d_tracklist, track_number, d_artists):
        '''gets Artist name from discogs release (child)objects via track_number, eg. A1'''
        for tr in d_tracklist:
            #log.info("d_artists_parse: this is the tr object: {}".format(dir(tr)))
            if tr.position == track_number:
                #log.info("d_tracklist_parse: found by track number.")
                if len(tr.artists) == 1:
                    name = tr.artists[0].name
                    log.info("MODEL: d_artists_parse: just one artist, returning name: {}".format(name))
                    return name
                elif len(tr.artists) == 0:
                    #log.info(
                    #  "MODEL: d_artists_parse: tr.artists len 0: this is it: {}".format(
                    #            dir(tr.artists)))
                    log.info(
                      "MODEL: d_artists_parse: no artists in tracklist, checking d_artists object..")
                    combined_name = self.d_artists_to_str(d_artists)
                    return combined_name
                else:
                    log.info("tr.artists len: {}".format(len(tr.artists)))
                    for a in tr.artists:
                        log.info("release.artists debug loop: {}".format(a.name))
                    combined_name = self.d_artists_to_str(tr.artists)
                    log.info(
                      "MODEL: d_artists_parse: several artists, returning combined named {}".format(
                        combined_name))
                    return combined_name

    def get_releases_of_one_mix(self, start_pos = False):
        if not start_pos:
            where = "mix_id == {}".format(self.id)
        else:
            where = "mix_id == {} and track_pos >= {}".format(self.id, start_pos)
        log.info("MODEL: Returning tracks of a mix.")
        return self._select_simple(['*'], 'mix_track', where,
                fetchone = False, orderby = 'track_pos')

    def get_tracks_by_bpm(self, bpm, pitch_range):
        min_bpm = bpm - (bpm / 100 * pitch_range)
        max_bpm = bpm + (bpm / 100 * pitch_range)
        sql_bpm = '''SELECT discogs_title, track.d_artist, d_track_name,
                           track.d_track_no, key, bpm, key_notes, notes FROM
                               release LEFT OUTER JOIN track
                               ON release.discogs_id = track.d_release_id
                                   INNER JOIN track_ext
                                   ON track.d_release_id = track_ext.d_release_id
                                   AND track.d_track_no = track_ext.d_track_no
                       WHERE (track_ext.bpm >= "{}" AND track_ext.bpm <= "{}")
                       ORDER BY track_ext.key, track_ext.bpm'''.format(min_bpm, max_bpm)
        return self._select(sql_bpm, fetchone = False)

    def get_tracks_by_key(self, key):
        prev_key = ""
        next_key = ""
        sql_key = '''SELECT discogs_title, track.d_artist, d_track_name,
                           track.d_track_no, key, bpm, key_notes, notes FROM
                               release LEFT OUTER JOIN track
                               ON release.discogs_id = track.d_release_id
                                   INNER JOIN track_ext
                                   ON track.d_release_id = track_ext.d_release_id
                                   AND track.d_track_no = track_ext.d_track_no
                       WHERE (track_ext.key LIKE "%{}%")
                       ORDER BY track_ext.key, track_ext.bpm'''.format(key)
        return self._select(sql_key, fetchone = False)

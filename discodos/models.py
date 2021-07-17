from discodos.utils import is_number  # most of this should only be in view
import logging
# import pprint
import discogs_client
import discogs_client.exceptions
import requests.exceptions
import urllib3.exceptions
from sqlite3 import Error as sqlerr
import sqlite3
import time
from datetime import datetime
import musicbrainzngs as m
from musicbrainzngs import WebServiceError
import requests
import json
import re
from socket import gaierror

log = logging.getLogger('discodos')


class Database (object):

    def __init__(self, db_conn=False, db_file=False, setup=False):
        self.db_not_found = False
        if db_conn:
            log.debug("DB-NEW: db_conn argument was handed over.")
            self.db_conn = db_conn
        else:
            log.debug("DB-NEW: Creating connection to db_file.")
            if not db_file:
                log.debug("DB-NEW: No db_file given, using default name.")
                db_file = './discobase.db'
            self.db_conn = self.create_conn(db_file, setup)  # setup=True creates empty db
            if self.db_conn is None:
                log.debug("DB-NEW: Creating database.")
                self.db_conn = self.create_conn(db_file, setup=True)
        self.db_conn.row_factory = sqlite3.Row  # also this was in each db.function before
        self.cur = self.db_conn.cursor()  # we had this in each db function before
        self.configure_db()  # set PRAGMA options

    def create_conn(self, db_file, setup=False):
        try:  # format ensures db_file is string. uri rw mode throws error if non-existen
            if setup:
                conn = sqlite3.connect('file:{}'.format(db_file), uri=True)
            else:
                conn = sqlite3.connect('file:{}?mode=rw'.format(db_file), uri=True)
            return conn
        except sqlerr as e:
            if e.args[0] == 'unable to open database file':
                e = "DB-NEW: create_conn: Database {} can't be opened.".format(db_file)
                log.debug(e)
                self.db_not_found = True
                return None
            else:
                log.error("DB-NEW: Connection error: %s", e)
                raise SystemExit(4)  # 4 = other db error. will SystemExit break gui?

    def execute_sql(self, sql, values_tuple=False, raise_err=False):
        '''used for eg. creating tables or inserts'''
        log.info("DB-NEW: execute_sql: %s", sql)
        try:
            with self.db_conn:  # auto commits and auto rolls back on exceptions
                c = self.cur  # connection close has to be done manually though!
                if values_tuple:
                    log.info("DB-NEW: ...with this tuple: {%s}", values_tuple)
                    c.execute(sql, values_tuple)
                else:
                    c.execute(sql)
                log.info("DB-NEW: rowcount: {}, lastrowid: {}".format(c.rowcount,
                         c.lastrowid))
                # log.info("DB-NEW: Committing NOW")
                # self.db_conn.commit()
            log.info("DB-NEW: Committing via context close NOW")
            self.lastrowid = c.lastrowid
            return c.rowcount
        except sqlerr as e:
            # log.error("DB-NEW: %s", dir(e))
            if raise_err:
                log.info("DB-NEW: Raising error to upper level.")
                raise e
            else:
                log.error("DB-NEW: %s", e.args[0])
            return False

    def configure_db(self):
        settings = "PRAGMA foreign_keys = ON;"
        self.execute_sql(settings)

    def _select_simple(self, fields_list, table, condition=False, offset=0,
                       fetchone=False, orderby=False, distinct=False):
        """This is a wrapper around the _select method.
           It puts together sql select statements as strings.
        """
        log.info("DB-NEW: _select_simple: fetchone = {}".format(fetchone))
        fields_str = ""
        for cnt, field in enumerate(fields_list):
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
        if distinct:
            select = 'SELECT DISTINCT'
        else:
            select = 'SELECT'
        if offset:
            limit = 'LIMIT -1 OFFSET {}'.format(offset)
        else:
            limit = ''
        select_str = "{} {} FROM {} {} {} {};".format(
            select, fields_str, table,
            where_or_not, orderby_or_not, limit)
        return self._select(select_str, fetchone)

    def _select(self, sql_select, fetchone=False):
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
            if fetchone:  # len will return column count
                log.info('DB-NEW: Found 1 row containing {} columns.'.format(len(rows.keys())))
            else:  # len will return rows count
                log.info('DB-NEW: Found {} rows containing {} columns.'.format(
                    len(rows), len(rows[0])))
            log.debug("DB-NEW: Returning row(s) as type: {}.".format(type(rows).__name__))
            return rows
        else:
            log.info('DB-NEW: Nothing found - Returning type: {}.'.format(type(rows).__name__))
            return rows  # was empty list before, now it's either empty list or NoneType

    def close_conn(self):  # manually close conn! - context manager (with) doesn't do it
        self.db_conn.close()

    def debug_db(self, db_return):
        # print(dbr.keys())
        print()
        for i in db_return:
            # print(i.keys())
            stringed = ''
            for j in i:
                stringed+='{}, '.format(j)
            print(stringed)
            print()
        return True


# mix model class
class Mix (Database):

    def __init__(self, db_conn, mix_name_or_id, db_file=False):
        super(Mix, self).__init__(db_conn, db_file)
        # figuring out names and IDs, just logs and sets instance
        # attributes, no exits here!
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
                self.name = self.info[1]  # info existing or trigger Exception?
                self.id_existing = True
                self.name_existing = True
            except Exception:
                log.info("Mix ID is not existing yet!")
        else:
            self.name = mix_name_or_id
            # if it's a mix-name, get the id unless it's "all"
            # (default value, should only show mix list)
            if not self.name == "all":
                try:
                    mix_id_tuple = self._get_mix_id(self.name)
                    log.debug('MODEL: mix_id_tuple type: %s',
                              type(mix_id_tuple).__name__)
                    self.id = mix_id_tuple[0]
                    self.id_existing = True
                    self.name_existing = True
                    # load basic mix-info from DB
                    try:
                        self.info = self.get_mix_info()
                        self.name = self.info[1]
                    except Exception:
                        log.info("Can't get mix info.")
                except Exception:
                    log.info("Can't get mix-name from ID. "
                             "Mix not existing yet?")
        if self.id_existing:
            self.created = self.info[2]
            self.played = self.info[4]
            self.venue = self.info[5]
        log.debug("MODEL: Mix info is {}.".format(self.info))
        log.debug("MODEL: Name is {}.".format(self.name))
        log.debug("MODEL: Played is {}.".format(self.played))
        log.debug("MODEL: Venue is {}.".format(self.venue))

    # FIXME mix info should probably be properties to keep them current
    # @property
    # def.name(self):
    #    return db.get_mix_info(self.db_conn, self.id)[1]

    def _get_mix_id(self, mixname):  # should only be called from __init__
        log.info('MODEL: Getting mix_id via mix name "%s". '
                 'Only returns first match', mixname)
        if is_number(mixname):
            log.info("MODEL: mix name is a number, won't try to fetch from DB")
            return mixname
        else:
            self.cur.execute(
                'SELECT mix_id FROM mix WHERE name LIKE ?',
                ("%{}%".format(mixname), )
            )
            row = self.cur.fetchone()
            if row:
                log.info("MODEL: Found mix ID: {}".format(row["mix_id"]))
                return row
            else:
                log.info("MODEL: Can't fetch mix ID by name")
                return row

    def delete(self):
        log.info('MODEL: Deleting mix %s and all its mix_track entries '
                 '(through cascade)', self.id)
        del_return = self.execute_sql(
            'DELETE FROM mix WHERE mix_id == ?',
            (self.id, )
        )
        log.info("MODEL: Deleted mix, DB returned: {}".format(del_return))
        self.id_existing = False
        self.name_existing = False  # it's deleted, name is available again
        self.info = []
        # self.name = False # keep name so we still know after delete
        self.created = False
        self.updated = False
        self.played = False
        self.venue = False
        return del_return

    def create(self, _played, _venue, new_mix_name=False):
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

    def get_all_mixes(self, order_by='played ASC'):
        """
        get metadata of all mixes from db

        @param
        @return sqlite fetchall rows object
        @author
        """
        # we want to select * but in a different order:
        log.info("MODEL: Getting mixes table.")
        mixes_data = self._select_simple(
            ['mix_id', 'name', 'played', 'venue', 'created', 'updated'],
            'mix', condition=False, orderby=order_by
        )
        return mixes_data

    def get_one_mix_track(self, track_id):
        log.info("MODEL: Returning track {} from mix {}.".format(
            track_id, self.id)
        )
        _where = 'mix_track.mix_id == {} AND mix_track.track_pos == {}'.format(
            self.id, track_id
        )
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
        return self._select_simple(
            ['track_pos', 'discogs_title', 'd_track_name',
             'mix_track.d_track_no', 'trans_rating', 'trans_notes', 'key',
             'key_notes', 'bpm', 'notes', 'mix_track_id',
             'mix_track.d_release_id', 'm_rec_id_override'],
            _join, fetchone=True, condition=_where
        )

    def update_mix_track_and_track_ext(self, track_details, edit_answers):
        log.info(
            "MODEL: Updating mix_track and track_ext entries (if necessary).")
        log.debug("MODEL: track_details dict: {}".format(track_details))
        log.debug("MODEL: edit_answers dict: {}".format(edit_answers))
        mix_track_cols=[
            'd_release_id', 'd_track_no', 'track_pos', 'trans_rating',
            'trans_notes'
        ]
        track_ext_cols=['key', 'bpm', 'key_notes', 'notes', 'm_rec_id_override']
        values_mix_track = ''  # mix_track update
        values_list_mix_track = []
        values_track_ext = ''  # track_ext update
        values_list_track_ext = []
        cols_insert_track_ext = ''  # track_ext insert
        values_insert_track_ext = ''  # (the tuple is the same obviously)

        mix_track_edit = False  # decide if it's table mix_track or track_ext
        track_ext_edit = False
        updated_mix_track = False  # save if we've updated mix_track table
        updated_track_ext = False  # save if we've updated track_ext table
        for key in edit_answers:
            if key in mix_track_cols:
                mix_track_edit = True
            if key in track_ext_cols:
                track_ext_edit = True

        if mix_track_edit:
            # save current track order if pos-edit included
            if 'track_pos' in edit_answers:
                move_to = int(edit_answers['track_pos'])
                # when moving the track "up"
                if move_to < track_details['track_pos']:
                    all_after_dest_pos = self.get_tracks_from_position(
                        edit_answers['track_pos'])
                    # shift all those tracks "down" +1
                    self.reorder_tracks_squeeze_in(
                        edit_answers['track_pos'],
                        all_after_dest_pos
                    )
                # when moving the track "down"
                elif move_to > track_details['track_pos']:
                    # we set dest pos to be one further down to really be the
                    # chosen destination after reorder_pos (see below db update)
                    edit_answers['track_pos'] = move_to + 1
                    all_after_dest_pos = self.get_tracks_from_position(
                        edit_answers['track_pos'])
                    # shift all those tracks "down" +1
                    self.reorder_tracks_squeeze_in(
                        edit_answers['track_pos'],
                        all_after_dest_pos)
                # no else: nothing to do if track_pos stays the same
                # FIXME somehow we should user inform like this:
                # this track will be put in after/bevore track "name" ok?

            update_mix_track = 'UPDATE mix_track SET '
            where_mix_track = 'WHERE mix_track_id == {}'.format(
                track_details['mix_track_id'])
            for key, answer in edit_answers.items():
                log.debug('key: {}, value: {}'.format(key, answer))
                if key in mix_track_cols:
                    if values_mix_track == '':
                        values_mix_track += "{} = ? ".format(key)
                    else:
                        values_mix_track += ", {} = ? ".format(key)
                    values_list_mix_track.append(answer)
            final_update_mix_track = update_mix_track + values_mix_track + where_mix_track
            # debug
            # log.info('MODEL: {}'.format(final_update_mix_track))
            # log.info(log.info('MODEL: {}'.format(tuple(values_list_mix_track))))

            log.info("MODEL: Now really executing mix_track update...")
            updated_mix_track = self.execute_sql(
                final_update_mix_track, tuple(values_list_mix_track))

            # finish "track moving":
            # after original track_pos was edited we fill in the gap
            if 'track_pos' in edit_answers:
                self.reorder_tracks(int(track_details['track_pos']) - 1)
            # FIXME no sanity check if this was ok

        if track_ext_edit:
            update_track_ext = 'UPDATE track_ext SET '
            insert_track_ext = 'INSERT INTO track_ext'
            where_track_ext = 'WHERE d_release_id == {} AND d_track_no == \"{}\"'.format(
                track_details['d_release_id'], track_details['d_track_no'])
            for key, answer in edit_answers.items():
                log.debug('key: {}, value: {}'.format(key, answer))
                if key in track_ext_cols:
                    if values_track_ext == '':
                        values_track_ext += "{} = ? ".format(key)
                    else:
                        values_track_ext += ", {} = ? ".format(key)
                    values_list_track_ext.append(answer)

                    if values_insert_track_ext == '':
                        cols_insert_track_ext += "{}".format(key)
                        values_insert_track_ext += "?"
                    else:
                        cols_insert_track_ext += ", {}".format(key)
                        values_insert_track_ext += ", ?"
                    # the list is the same as with update

            final_update_track_ext = update_track_ext + values_track_ext + where_track_ext
            final_insert_track_ext = "{} ({}, d_release_id, d_track_no) VALUES ({}, ?, ?)".format(
                insert_track_ext, cols_insert_track_ext, values_insert_track_ext)

            # debug
            # log.info('MODEL: {}'.format(final_update_track_ext))
            # log.info('MODEL: {}'.format(tuple(values_list_track_ext)))

            # log.info('MODEL: {}'.format(final_insert_track_ext))
            values_insert_list_track_ext = values_list_track_ext[:]
            values_insert_list_track_ext.append(track_details['d_release_id'])
            values_insert_list_track_ext.append(track_details['d_track_no'])
            # log.info('MODEL: {}'.format(tuple(values_insert_list_track_ext)))

            log.info("MODEL: Now really executing track_ext update/insert...")
            # log.info(values_list_track_ext)
            # log.info(tuple(values_list_track_ext))

            dbret = self.execute_sql(
                final_update_track_ext,
                tuple(values_list_track_ext)
            )
            if dbret == 0:  # checks rowcount
                log.info("MODEL: UPDATE didn't change anything, "
                         "trying INSERT...")
                dbret = self.execute_sql(
                    final_insert_track_ext,
                    tuple(values_insert_list_track_ext)
                )
            updated_track_ext = dbret

        # finally update mix table with current timestamp (only if changed)
        if updated_mix_track or updated_track_ext:
            return self._updated_timestamp()
        return True  # we didn't update track nor track_ext - all good

    def _updated_timestamp(self):
        return self.execute_sql(
            """
            UPDATE mix SET
              updated = datetime('now', 'localtime') WHERE mix_id == ?;""",
            (self.id, )
        )

    def get_tracks_from_position(self, pos):
        log.info('MODEL: Getting tracks in mix, '
                 'starting at position {}.'.format(pos))
        # return db.get_tracks_from_position(self.db_conn, self.id, pos)
        return self._select_simple(
            ['mix_track_id', 'track_pos'], 'mix_track',
            condition="mix_id = {} AND track_pos >= {}".format(self.id, pos),
            orderby='track_pos ASC'
        )

    def reorder_tracks(self, pos):
        log.info("MODEL: Reordering tracks in mix, "
                 "starting at pos {}".format(pos))
        tracks_to_shift = self.get_tracks_from_position(pos)
        if not tracks_to_shift:
            return False
        for t in tracks_to_shift:
            log.info("MODEL: Shifting mix_track_id %i from pos %i to %i",
                     t['mix_track_id'], t['track_pos'], pos)
            sql_upd = '''
                UPDATE mix_track SET track_pos = ?
                  WHERE mix_track_id == ?'''
            ids_tuple = (pos, t['mix_track_id'])
            if not self.execute_sql(sql_upd, ids_tuple):
                return False
            pos = pos + 1
        return self._updated_timestamp()

    def reorder_tracks_squeeze_in(self, pos, tracks_to_shift):
        log.info("MODEL: Reordering because a track was squeezed in at pos "
                 "{}.".format(pos))
        if not tracks_to_shift:
            return False
        for t in tracks_to_shift:
            new_pos = t['track_pos'] + 1
            log.info("MODEL: Shifting mix_track_id %i from pos %i to %i",
                     t['mix_track_id'], t['track_pos'], new_pos)
            sql_upd = 'UPDATE mix_track SET track_pos = ? WHERE mix_track_id == ?'
            ids_tuple = (new_pos, t['mix_track_id'])
            if not self.execute_sql(sql_upd, ids_tuple):
                return False
        return self._updated_timestamp()

    def shift_track(self, pos, direction):
        if direction != 'up' and direction != 'down':
            log.error('MODEL: shift_track: wrong usage.')
            return False
        # get mix_track_id of track to shift, the one before and the one after
        tr_before = self._select_simple(
            ['mix_track_id'], 'mix_track', fetchone=True,
            condition="mix_id = {} AND track_pos == {}".format(self.id, pos - 1)
        )
        tr = self._select_simple(
            ['mix_track_id'], 'mix_track', fetchone=True,
            condition="mix_id = {} AND track_pos == {}".format(self.id, pos)
        )
        tr_after = self._select_simple(
            ['mix_track_id'], 'mix_track', fetchone=True,
            condition="mix_id = {} AND track_pos == {}".format(self.id, pos + 1)
        )
        log.debug('before: {}, shift_track: {}, after: {}'.format(
            tr_before['mix_track_id'], tr['mix_track_id'],
            tr_after['mix_track_id'])
        )

        if direction == 'up':
            tr_before_pos = pos       # is now the same as the orig track
            tr_pos = pos - 1          # is now one less than before
            # tr_after_pos = pos + 1  # stays the same

            sql_upd_tr_bef = 'UPDATE mix_track SET track_pos = ? WHERE mix_track_id == ?'
            ids_tr_bef = (tr_before_pos, tr_before['mix_track_id'])
            sql_upd_tr = 'UPDATE mix_track SET track_pos = ? WHERE mix_track_id == ?'
            ids_tr = (tr_pos, tr['mix_track_id'])

            ret_tr = self.execute_sql(sql_upd_tr, ids_tr)
            ret_tr_bef = self.execute_sql(sql_upd_tr_bef, ids_tr_bef)
            ret_tr_aft = True

        elif direction == 'down':
            # tr_before_pos = pos - 1  # stays the same
            tr_pos = pos + 1           # is now one more than before
            tr_after_pos = pos         # is now the same as the orig track

            sql_upd_tr = 'UPDATE mix_track SET track_pos = ? WHERE mix_track_id == ?'
            ids_tr = (tr_pos, tr['mix_track_id'])
            sql_upd_tr_aft = 'UPDATE mix_track SET track_pos = ? WHERE mix_track_id == ?'
            ids_tr_aft = (tr_after_pos, tr_after['mix_track_id'])

            ret_tr_bef = True
            ret_tr = self.execute_sql(sql_upd_tr, ids_tr)
            ret_tr_aft = self.execute_sql(sql_upd_tr_aft, ids_tr_aft)

        if not ret_tr and ret_tr_bef and ret_tr_aft:
            log.error('MODEL: shift_track: one or more track updates failed.')
            return False
        log.info(
            'MODEL: shift_track: Former track {} was successfully '.format(pos)
            + 'shifted {}.'.format(direction)
        )
        return self._updated_timestamp()

    def delete_track(self, pos):
        log.info("MODEL: Deleting track {} from {}.".format(pos, self.id))
        sql_del = 'DELETE FROM mix_track WHERE mix_id == ? AND track_pos == ?'
        ids_tuple = (self.id, pos)
        del_success = self.execute_sql(sql_del, (ids_tuple))
        if del_success:
            return self._updated_timestamp()
        return del_success

    def get_full_mix(self, verbose=False, brainz=False,
                     order_by='track_pos ASC'):
        log.info('MODEL: Getting full mix.')
        if verbose:
            sql_sel = '''SELECT track_pos, discogs_title, track.d_artist,
                           d_track_name, mix_track.d_track_no, key, bpm,
                           key_notes, trans_rating, trans_notes, notes, a_key,
                           a_chords_key, a_bpm FROM'''
        elif brainz:
            sql_sel = '''SELECT track_pos, discogs_title, mix_track.d_track_no,
                           key, bpm, a_key, a_chords_key, a_bpm,
                           d_catno, discogs_id, m_rel_id, m_rec_id,
                           m_rel_id_override, m_rec_id_override,
                           track.m_match_method AS track_match_method,
                           release.m_match_method AS release_match_method,
                           release.m_match_time AS release_match_time,
                           track.m_match_time AS track_match_time FROM'''
        else:
            sql_sel = '''SELECT track_pos, d_catno, discogs_title,
                           mix_track.d_track_no, trans_rating, key, bpm, a_key,
                           a_chords_key, a_bpm FROM'''

        order_clause = 'ORDER BY {}'.format(order_by)
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
                        {}'''.format(self.id, order_clause)
        return self._select(sql_sel, fetchone=False)

    def add_track(self, release_id, track_no, track_pos, trans_rating='', trans_notes=''):
        log.info('MODEL: Adding track to current mix.')
        log.debug("MODEL: add_track got this: mix_id: {}, d_release_id: {}, track_no: {}, track_pos: {}, trans_rating: {}, trans_notes: {}".format(
            self.id, release_id, track_no, track_pos, trans_rating, trans_notes))
        track_no = track_no.upper()  # always save uppercase track numbers
        sql_add = '''INSERT INTO mix_track
            (mix_id, d_release_id, d_track_no, track_pos, trans_rating, trans_notes)
            VALUES(?, ?, ?, ?, ?, ?)'''
        values = (self.id, release_id, track_no, track_pos, trans_rating, trans_notes)
        add_success = self.execute_sql(sql_add, values)  # returns rowcount
        if add_success:
            return self._updated_timestamp()
        return add_success

    def get_last_track(self):
        log.info('MODEL: Getting last track in current mix')
        return self._select_simple(['MAX(track_pos)'], 'mix_track',
            condition="mix_id = {}".format(self.id), fetchone=True)

    def get_tracks_of_one_mix(self, start_pos=False):
        log.info("MODEL: Getting tracks of a mix, from mix_track_table only)")
        if not start_pos:
            where = "mix_id == {}".format(self.id)
        else:
            where = "mix_id == {} and track_pos >= {}".format(self.id, start_pos)
        return self._select_simple(['*'], 'mix_track', where,
                fetchone=False, orderby='track_pos')

    def get_all_tracks_in_mixes(self):
        log.info('MODEL: Getting all tracks from mix_track table (only).')
        return self._select_simple(['*'], 'mix_track', fetchone=False)

    def get_mix_info(self):
        log.info("MODEL: Getting mix info.")
        """
        get metadata of ONE mix from db

        @param
        @return sqlite fetchone rows object
        @author
        """
        self.mix_info = self._select_simple(
            ['*'], 'mix', "mix_id == {}".format(self.id), fetchone=True)
        return self.mix_info

    def update_mix_info(self, mix_details, edit_answers):
        log.info("MODEL: Updating mix table.")
        log.debug("MODEL: mix_details dict: {}".format(mix_details))
        log.debug("MODEL: edit_answers dict: {}".format(edit_answers))
        values_mix = ''
        values_list_mix = []

        update_mix = 'UPDATE mix SET '
        where_mix = 'WHERE mix_id == {}'.format(mix_details['mix_id'])
        for key, answer in edit_answers.items():
            log.debug('key: {}, value: {}'.format(key, answer))
            # handle slq col = ?
            if values_mix == '':
                values_mix += "{} = ? ".format(key)
            else:
                values_mix += ", {} = ? ".format(key)
            # handle values list (later tuple)
            values_list_mix.append(answer)
            values_mix += ", updated = datetime('now', 'localtime') "

        if len(edit_answers) != 0:  # only update if necessary
            final_update_mix = update_mix + values_mix + where_mix
            log.info("MODEL: Executing mix update...")
            return self.execute_sql(final_update_mix, tuple(values_list_mix))
        else:
            log.info("MODEL: Nothing changed - not executing mix update")
            return True

    def get_mix_tracks_for_brainz_update(self, start_pos=False):
        log.info("MODEL: Getting tracks of a mix. Preparing for Discogs or AcousticBrainz update.")
        if not start_pos:
            where = "mix_id == {}".format(self.id)
        else:
            where = "mix_id == {} and track_pos >= {}".format(
                self.id, start_pos)
        tables = '''mix_track
                      INNER JOIN release
                      ON mix_track.d_release_id = release.discogs_id
                        LEFT OUTER JOIN track
                        ON mix_track.d_release_id = track.d_release_id
                        AND mix_track.d_track_no = track.d_track_no
                          LEFT OUTER JOIN track_ext
                          ON mix_track.d_release_id = track_ext.d_release_id
                          AND mix_track.d_track_no = track_ext.d_track_no'''
        return self._select_simple(['track_pos', 'mix_track.d_release_id',
          'discogs_id', 'discogs_title', 'd_catno', 'track.d_artist',
          'd_track_name', 'mix_track.d_track_no', 'm_rec_id_override'],
           tables, where, fetchone=False, orderby='mix_track.track_pos')

    def get_all_mix_tracks_for_brainz_update(self, offset=0):
        log.info("MODEL: Getting all tracks of all mix. Preparing for Discogs or AcousticBrainz update.")
        if offset > 0:
            log.info('MODEL: Add 1 to offset (FIXME why?)')
            offset = offset - 1
        tables = '''mix_track
                      INNER JOIN release
                      ON mix_track.d_release_id = release.discogs_id
                        LEFT OUTER JOIN track
                        ON mix_track.d_release_id = track.d_release_id
                        AND mix_track.d_track_no = track.d_track_no
                          LEFT OUTER JOIN track_ext
                          ON mix_track.d_release_id = track_ext.d_release_id
                          AND mix_track.d_track_no = track_ext.d_track_no'''
        return self._select_simple(['track_pos', 'mix_track.d_release_id',
          'discogs_id', 'discogs_title', 'd_catno', 'track.d_artist',
          'd_track_name', 'mix_track.d_track_no', 'm_rec_id_override'],
           tables, fetchone=False, distinct=True, offset=offset,
           orderby='mix_track.mix_id, mix_track.track_pos')


# record collection class
class Collection (Database):

    def __init__(self, db_conn, db_file=False):
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
                    user_token=_userToken)
            self.me = self.d.identity()
            global d
            d = self.d
            global me
            me = self.me
            _ONLINE = True
        # except Exception as Exc:
        except Exception:
            _ONLINE = False
            # raise Exc
        self.ONLINE = _ONLINE
        return _ONLINE

    def get_all_db_releases(self):
        # return db.all_releases(self.db_conn)
        return self._select_simple(['d_catno', 'd_artist',
            'discogs_title', 'discogs_id', 'm_rel_id', 'm_rel_id_override'
            # 'import_timestamp', 'in_d_collection'], 'release', orderby='d_artist, discogs_title')
            ], 'release', orderby='d_artist, discogs_title')

    def search_release_online(self, id_or_title):
        try:
            if is_number(id_or_title):
                releases = [self.d.release(id_or_title)]
            else:
                releases = self.d.search(id_or_title, type='release')
            # exceptions are only triggerd if trying to access the release obj
            if len(releases) > 0:  # fixes list index error
                log.info("First found release: {}".format(releases[0]))
            log.debug("All found releases: {}".format(releases))
            return releases
        except discogs_client.exceptions.HTTPError as HtErr:
            log.error("%s (HTTPError)", HtErr)
            return None
        except urllib3.exceptions.NewConnectionError as ConnErr:
            log.error("%s (NewConnectionError)", ConnErr)
            return None
        except urllib3.exceptions.MaxRetryError as RetryErr:
            log.error("%s (MaxRetryError)", RetryErr)
            return None
        except requests.exceptions.ConnectionError as ConnErr:
            log.error("%s (ConnectionError)", ConnErr)
            return None
        except gaierror as GaiErr:
            log.error("%s (socket.gaierror)", GaiErr)
            return None
        except TypeError as TypeErr:
            log.error("%s (TypeError)", TypeErr)
            return None
        except Exception as Exc:
            log.error("%s (Exception)", Exc)
            raise Exc
            return None

    def prepare_release_info(self, release):  # discogs_client Release object
        '''takes a discogs_client Release object and returns prepares "relevant"
           data into a dict with named keys. We use it eg for a nicely formatted
           release view using tabulate'''
        rel_details={}
        rel_details['id'] = release.id
        rel_details['artist'] = release.artists[0].name
        rel_details['title'] = release.title
        if len(release.labels) != 0:
            rel_details['label'] = release.labels[0].name
        rel_details['country'] = release.country
        rel_details['year'] = release.year
        rel_details['format'] = release.formats[0]['descriptions'][0]
        if len(release.formats[0]['descriptions']) > 1:
            rel_details['format'] += ' {}'.format(
                  release.formats[0]['descriptions'][1])

        log.info("prepare_release_info: rel_details: {}".format(
            rel_details))
        return rel_details

    def prepare_tracklist_info(self, release_id, tracklist):  # discogs_client tracklist object
        '''takes a tracklist (just a list?) we received from a Discogs release
            object and adds additional information from the database 
            into the list'''
        tl=[]
        for i, track in enumerate(tracklist):
            dbtrack = self.get_track(release_id, track.position)
            if dbtrack == None:
                log.debug(
                 "prepare_tracklist_info: Track not in DB. Adding title/track_no only.")
                tl.append({
                    'track_no': track.position,
                    'track_title': track.title
                })
            else:
                tl.append({
                    'track_no': track.position,
                    'track_title': track.title,
                    'key': dbtrack['key'],
                    'key_notes': dbtrack['key_notes'],
                    'bpm': dbtrack['bpm'],
                    'notes': dbtrack['notes'],
                    'a_key': dbtrack['a_key'],
                    'a_chords_key': dbtrack['a_chords_key'],
                    'a_bpm': dbtrack['a_bpm']
                })
        return tl

    def get_track(self, release_id, track_no):
        log.info("MODEL: Returning collection track {} from release {}.".format(
              track_no, release_id))
        where = 'track.d_release_id == {} AND track.d_track_no == "{}"'.format(
              release_id, track_no.upper())  # we always save track_nos uppercase
        join = '''track LEFT OUTER JOIN track_ext
                    ON track.d_release_id = track_ext.d_release_id
                    AND track.d_track_no = track_ext.d_track_no'''
        return self._select_simple(['track.d_track_no', 'track.d_release_id',
          'd_track_name', 'key', 'key_notes', 'bpm', 'notes', 'm_rec_id_override',
          'a_key', 'a_chords_key', 'a_bpm'],
          join, fetchone=True, condition=where)

    def search_release_offline(self, id_or_title):
        if is_number(id_or_title):
            try:
                return self.search_release_id(id_or_title)
            except Exception as Exc:
                log.error("Not found or Database Exception: %s\n", Exc)
                raise Exc
        else:
            try:
                releases = self._select_simple(['*'], 'release',
                        'discogs_title LIKE "%{}%" OR d_artist LIKE "%{}%"'.format(
                        id_or_title, id_or_title), fetchone=False, orderby='d_artist')
                if releases:
                    log.debug("First found release: {}".format(releases[0]))
                    log.debug("All found releases: {}".format(releases))
                    return releases  # this is a list
                else:
                    return None
            except Exception as Exc:
                log.error("Not found or Database Exception: %s\n", Exc)
                raise Exc

    def search_release_track_offline(self, artist='', release='', track=''):
        fields = ['release.d_artist', 'track.d_artist', 'track.d_release_id',
                  'release.d_catno', 'release.discogs_title',
                  'release.import_timestamp', 'release.in_d_collection',
                  'release.m_rel_id', 'release.m_rel_id_override',
                  'release.m_match_method', 'release.m_match_time',
                  'track.d_track_no', 'track.d_track_name', 'track_ext.key',
                  'track_ext.bpm', 'track_ext.key_notes', 'track_ext.notes']
        from_tables='''
                    release LEFT OUTER JOIN track
                    ON track.d_release_id = release.discogs_id
                      LEFT OUTER JOIN track_ext
                      ON track.d_release_id = track_ext.d_release_id
                      AND track.d_track_no = track_ext.d_track_no'''

        if not artist:
            artist_sql = '''
                ((track.d_artist IS NULL OR track.d_artist LIKE "%") OR
                 (release.d_artist IS NULL OR release.d_artist LIKE "%"))'''
        else:
            artist_sql = '(track.d_artist LIKE "%{}%" OR release.d_artist LIKE "%{}%")'.format(
                artist, artist)

        if not release:
            release_sql = '(discogs_title IS NULL OR discogs_title LIKE "%")'
        else:
            release_sql = 'discogs_title LIKE "%{}%"'.format(release)

        if not track:
            track_sql = '(d_track_name IS NULL OR d_track_name LIKE "%")'
        else:
            track_sql = 'd_track_name LIKE "%{}%"'.format(track)

        where = '''{} AND {} AND {}'''.format(
            artist_sql, release_sql, track_sql
        )
        order_by = 'track.d_artist, discogs_title, d_track_name'

        # prevent returning whole track collection when all search params empty
        if not artist and not release and not track:
            tracks = []
        else:
            tracks = self._select_simple(
                fields, from_tables, where, fetchone=False, orderby=order_by
            )
        # log.debug(self.debug_db(tracks))
        return tracks

    def upsert_track(self, release_id, track_no, track_name, track_artist):
        track_no = track_no.upper()  # always save uppercase track numbers
        try:
            sql_i='''INSERT INTO track(d_release_id, d_track_no, d_artist,
                        d_track_name, import_timestamp)
                        VALUES(?, ?, ?, ?, datetime('now', 'localtime'));'''
            tuple_i = (release_id, track_no, track_artist, track_name)
            return self.execute_sql(sql_i, tuple_i, raise_err=True)
        except sqlerr as e:
            if "UNIQUE constraint failed" in e.args[0]:
                log.debug("Track already in DiscoBASE, updating ...")
                try:
                    sql_u='''UPDATE track SET
                                d_artist = ?, d_track_name = ?,
                                import_timestamp=datetime('now', 'localtime')
                                WHERE d_release_id = ? AND d_track_no = ?;'''
                    tuple_u = (track_artist, track_name, release_id, track_no)
                    return self.execute_sql(sql_u, tuple_u, raise_err=True)
                except sqlerr as e:
                    log.error("MODEL: upsert_track: %s", e.args[0])
                    return False
            else:
                log.error("MODEL: %s", e.args[0])
                return False

    def search_release_id(self, release_id):
        return self._select_simple(['*'], 'release',
            'discogs_id == {}'.format(release_id), fetchone=True)

    def create_release(self, release_id, release_title, release_artists, d_catno, d_coll=False):
        try:
            insert_sql = '''INSERT OR FAIL INTO release(discogs_id, discogs_title,
                                    import_timestamp, d_artist, in_d_collection, d_catno)
                                    VALUES(?, ?, ?, ?, ?, ?)'''
            in_tuple = (release_id, release_title, datetime.today().isoformat(' ', 'seconds'),
                    release_artists, d_coll, d_catno)
            return self.execute_sql(insert_sql, in_tuple, raise_err=True)
        except sqlerr as e:
            if "UNIQUE constraint failed" in e.args[0]:
                log.debug("Release already in DiscoBASE, updating ...")
                try:
                    upd_sql = '''UPDATE release SET (discogs_title,
                        import_timestamp, d_artist, in_d_collection, d_catno)
                        = (?, ?, ?, ?, ?) WHERE discogs_id == ?;'''
                    upd_tuple = (release_title, datetime.today().isoformat(' ', 'seconds'),
                        release_artists, d_coll, d_catno, release_id)
                    return self.execute_sql(upd_sql, upd_tuple, raise_err = True)
                except sqlerr as e:
                    log.error("MODEL: create_release: %s", e.args[0])
                    return False
            else:
                log.error("MODEL: %s", e.args[0])
                return False

    def get_d_release(self, release_id, catch=True):
        try:
            r = self.d.release(release_id)
            if catch == True:
                log.debug("try to access r here to catch err {}".format(r.title))
            return r
        except discogs_client.exceptions.HTTPError as HtErr:
            log.error('Release not existing on Discogs ({})'.format(HtErr))
            return False
        except urllib3.exceptions.NewConnectionError as ConnErr:
            log.error("%s", ConnErr)
            return False
        except urllib3.exceptions.MaxRetryError as RetryErr:
            log.error("%s", RetryErr)
            return False
        except Exception as Exc:
            log.error("Exception: %s", Exc)
            return False

    def is_in_d_coll(self, release_id):
        # successful = False
        for r in self.me.collection_folders[0].releases:
            # self.rate_limit_slow_downer(d, remaining=5, sleep=2)
            if r.release.id == release_id:
                return r
        return False

    def rate_limit_slow_downer(self, remaining=10, sleep=2):
        '''Discogs util: stay in 60/min rate limit'''
        if int(self.d._fetcher.rate_limit_remaining) < remaining:
            log.info(
             "Discogs request rate limit is about to exceed, let's wait a little: %s",
                          self.d._fetcher.rate_limit_remaining)
            # while int(self.d._fetcher.rate_limit_remaining) < remaining:
            time.sleep(sleep)
        else:
            log.info("Discogs rate limit: %s remaining.",
                          self.d._fetcher.rate_limit_remaining)

    def track_report_snippet(self, track_pos, mix_id):
        track_pos_before = track_pos - 1
        track_pos_after = track_pos + 1
        sql_sel = '''SELECT track_pos, discogs_title, track.d_artist, d_track_name,
                           mix_track.d_track_no,
                           key, bpm, key_notes, trans_rating, trans_notes, notes,
                           a_key, a_chords_key, a_bpm FROM'''
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
            # self.cli.print_help(tracks_snippet)
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
        for cnt, artist in enumerate(d_artists):
            if cnt == 0:
                artist_str = artist.name
            else:
                artist_str += ' / {}'.format(artist.name)
        log.info('MODEL: combined artistlist to string \"{}\"'.format(artist_str))
        return artist_str

    def d_artists_parse(self, d_tracklist, track_number, d_artists):
        '''gets Artist name from discogs release (child)objects via track_number, eg. A1
           params d_artist: FIXME'''
        for tr in d_tracklist:
            # log.debug("d_artists_parse: this is the tr object: {}".format(dir(tr)))
            # log.debug("d_artists_parse: this is the tr object: {}".format(tr))
            if tr.position.upper() == track_number.upper():
                # log.info("d_tracklist_parse: found by track number.")
                if len(tr.artists) == 1:
                    name = tr.artists[0].name
                    log.info("MODEL: d_artists_parse: just one artist, returning name: {}".format(name))
                    return name
                elif len(tr.artists) == 0:
                    # log.info(
                    #   "MODEL: d_artists_parse: tr.artists len 0: this is it: {}".format(
                    #             dir(tr.artists)))
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
        log.debug('d_artists_parse: Track {} not existing on release.'.format(
            track_number))

    def d_tracklist_parse(self, d_tracklist, track_number):
        '''gets Track name from discogs tracklist object via track_number, eg. A1'''
        for tr in d_tracklist:
            # log.debug("d_tracklist_parse: this is the tr object: {}".format(dir(tr)))
            # log.debug("d_tracklist_parse: this is the tr object: {}".format(tr))
            if track_number != None:  # don't fail but return False
                if tr.position.upper() == track_number.upper():
                    return tr.title
        log.debug('d_tracklist_parse: Track {} not existing on release.'.format(
            track_number))
        return False  # we didn't find the tracknumber

    def d_tracklist_parse_numerical(self, d_tracklist, track_number):
        '''get numerical track pos from discogs tracklist object via
           track_number, eg. A1'''
        for num, tr in enumerate(d_tracklist):
            if tr.position.lower() == track_number.lower():
                return num + 1  # return human readable (matches brainz position)
        log.debug(
            'd_tracklist_parse_numerical: Track {} not existing on release.'.format(
              track_number))
        return False  # we didn't find the tracknumber

    def get_tracks_by_bpm(self, bpm, pitch_range):
        min_bpm = bpm - (bpm / 100 * pitch_range)
        max_bpm = bpm + (bpm / 100 * pitch_range)
        sql_bpm = '''
          SELECT discogs_title, d_catno, track.d_artist, d_track_name,
              track.d_track_no, key_notes, notes,
            CASE
                WHEN track_ext.bpm IS NOT NULL
                    THEN round(track_ext.bpm, 1)
                WHEN track.a_bpm IS NOT NULL
                    THEN round(track.a_bpm, 1)
            END AS chosen_bpm,
            CASE
                WHEN track_ext.key IS NOT NULL
                    THEN track_ext.key
                WHEN track.a_key IS NOT NULL
                    THEN track.a_key
            END AS chosen_key,
            CASE
                WHEN track.a_chords_key IS NOT NULL
                    THEN round(track.a_chords_key, 1)
            END AS chosen_chords_key
            FROM release LEFT OUTER JOIN track
                ON release.discogs_id = track.d_release_id
                    INNER JOIN track_ext
                    ON track.d_release_id = track_ext.d_release_id
                    AND track.d_track_no = track_ext.d_track_no
            WHERE
                (chosen_bpm >= {} AND chosen_bpm <= {})
                OR (chosen_bpm >= "{}" AND chosen_bpm <= "{}")
            ORDER BY chosen_key, chosen_bpm'''.format(
              min_bpm, max_bpm, min_bpm, max_bpm)
                    # THEN trim(track_ext.bpm, '.0')
                    # THEN trim(round(track.a_bpm, 0), '.0')
        return self._select(sql_bpm, fetchone=False)

    def get_tracks_by_key(self, key):
        # prev_key = "" # future music ;-) when we have key-translation-table
        # next_key = ""
        sql_key = '''
          SELECT discogs_title, d_catno, track.d_artist, d_track_name,
            track.d_track_no, key_notes, notes,
            CASE
                WHEN track_ext.bpm IS NOT NULL
                    THEN round(track_ext.bpm, 1)
                WHEN track.a_bpm IS NOT NULL
                    THEN round(track.a_bpm, 1)
            END AS chosen_bpm,
            CASE
                WHEN track_ext.key IS NOT NULL
                    THEN track_ext.key
                WHEN track.a_key IS NOT NULL
                    THEN track.a_key
            END AS chosen_key,
            CASE
                WHEN track.a_chords_key IS NOT NULL
                    THEN round(track.a_chords_key, 1)
            END AS chosen_chords_key
                FROM release LEFT OUTER JOIN track
                    ON release.discogs_id = track.d_release_id
                        INNER JOIN track_ext
                        ON track.d_release_id = track_ext.d_release_id
                        AND track.d_track_no = track_ext.d_track_no
            WHERE
                chosen_key LIKE "%{}%"
            ORDER BY chosen_key, chosen_bpm'''.format(key)
                   # THEN trim(round(track.a_bpm, 0), '.0')
                   # THEN round(track_ext.bpm, 0)
        return self._select(sql_key, fetchone=False)

    def get_tracks_by_key_and_bpm(self, key, bpm, pitch_range):
        min_bpm = bpm - (bpm / 100 * pitch_range)
        max_bpm = bpm + (bpm / 100 * pitch_range)
        sql_bpm = '''
          SELECT discogs_title, d_catno, track.d_artist, d_track_name,
              track.d_track_no, key_notes, notes,
            CASE
                WHEN track_ext.bpm IS NOT NULL
                    THEN round(track_ext.bpm, 1)
                WHEN track.a_bpm IS NOT NULL
                    THEN round(track.a_bpm, 1)
            END AS chosen_bpm,
            CASE
                WHEN track_ext.key IS NOT NULL
                    THEN track_ext.key
                WHEN track.a_key IS NOT NULL
                    THEN track.a_key
            END AS chosen_key,
            CASE
                WHEN track.a_chords_key IS NOT NULL
                    THEN round(track.a_chords_key, 1)
            END AS chosen_chords_key
            FROM release LEFT OUTER JOIN track
                ON release.discogs_id = track.d_release_id
                    INNER JOIN track_ext
                    ON track.d_release_id = track_ext.d_release_id
                    AND track.d_track_no = track_ext.d_track_no
            WHERE (chosen_bpm >= {} AND chosen_bpm <= {}
                  OR (chosen_bpm >= "{}" AND chosen_bpm <= "{}")
                   AND chosen_key LIKE "%{}%")
            ORDER BY chosen_key, chosen_bpm'''.format(min_bpm, max_bpm,
              min_bpm, max_bpm, key)
        return self._select(sql_bpm, fetchone=False)

    def upsert_track_brainz(self, release_id, track_no, rec_id,
          match_method, key, chords_key, bpm):
        track_no = track_no.upper()  # always save uppercase track numbers
        try:
            sql_i = '''INSERT INTO track(d_release_id, d_track_no,
                  m_rec_id, m_match_method, m_match_time, a_key, a_chords_key, a_bpm)
                  VALUES(?, ?, ?, ?, datetime('now', 'localtime'), ?, ?, ?);'''
            tuple_i = (release_id, track_no, rec_id, match_method, key,
                  chords_key, bpm)
            return self.execute_sql(sql_i, tuple_i, raise_err=True)
        except sqlerr as e:
            if "UNIQUE constraint failed" in e.args[0]:
                log.debug("Track already in DiscoBASE, updating ...")
                try:
                    sql_u = ''' UPDATE track SET
                          m_rec_id=?, m_match_method=?,
                          m_match_time=datetime('now', 'localtime'),
                          a_key=?, a_chords_key=?, a_bpm=?
                          WHERE d_release_id=? AND d_track_no=?; 
                          '''
                    tuple_u = (rec_id, match_method, key, chords_key, bpm,
                          release_id, track_no)
                    return self.execute_sql(sql_u, tuple_u)
                except sqlerr as e:
                    log.error("MODEL: create_release: %s", e.args[0])
                    return False
            else:
                log.error("MODEL: %s", e.args[0])
                return False

    def update_release_brainz(self, release_id, mbid, match_method):
        sql_upd = '''UPDATE release SET (m_rel_id, m_match_method,
                       m_match_time) = (?, ?, datetime('now', 'localtime'))
                       WHERE discogs_id == ?;'''
        tuple_upd = (mbid, match_method, release_id)
        return self.execute_sql(sql_upd, tuple_upd)

    def stats_match_method_release(self):
        sql_stats = '''
                    SELECT m_match_method, COUNT(*) FROM release GROUP BY m_match_method;
                    '''
        return self._select(sql_stats, fetchone=False)

    def d_get_first_catno(self, d_labels):
        '''get first found catalog number from discogs label object'''
        catno_str = ''
        if len(d_labels) == 0:
            log.warning(
              'MODEL: Discogs release without Label/CatNo. This is weird!')
        else:
            for cnt, label in enumerate(d_labels):
                if cnt == 0:
                    catno_str = label.data['catno']
                else:
                    log.warning('MODEL: Found multiple CatNos, not adding "{}"'.format(
                      label.data['catno']))
            log.info('MODEL: Found Discogs CatNo "{}"'.format(catno_str))
        return catno_str

    def d_get_all_catnos(self, d_labels):
        '''get all found catalog number from discogs label object concatinated
           with newline'''
        catno_str = ''
        if len(d_labels) == 0:
            log.warning(
              'MODEL: Discogs release without Label/CatNo. This is weird!')
        else:
            for cnt, label in enumerate(d_labels):
                if cnt == 0:
                    catno_str = label.data['catno']
                else:
                    catno_str += '\n{}'.format(label.data['catno'])
            log.info('MODEL: Found Discogs CatNo(s) "{}"'.format(catno_str))
        return catno_str

    def get_all_tracks_for_brainz_update(self, offset=0):
        log.info(
           "MODEL: Getting _all_ tracks in DiscoBASE. Preparing for AcousticBrainz update.")
        if offset > 0:
            log.info('MODEL: Subtract 1 from offset (eg --resume 1 should not alter anything')
            offset = offset - 1
        tables = '''release
                      LEFT OUTER JOIN track
                      ON release.discogs_id = track.d_release_id
                        LEFT OUTER JOIN track_ext
                        ON track.d_release_id = track_ext.d_release_id
                        AND track.d_track_no = track_ext.d_track_no'''
        return self._select_simple(['release.discogs_id',
              'track.d_release_id', 'discogs_title', 'd_catno',
              'track.d_artist', 'track.d_track_name', 'track.d_track_no',
              'track_ext.m_rec_id_override'], tables, condition=False,
               fetchone=False, orderby='release.discogs_id', offset=offset)

    def get_track_for_brainz_update(self, rel_id, track_no):
        log.info(
           "MODEL: Getting track. Preparing for AcousticBrainz update.")
        where = 'track.d_release_id == {} AND track.d_track_no == "{}"'.format(
            rel_id, track_no)
        tables = '''release
                      LEFT OUTER JOIN track
                      ON release.discogs_id = track.d_release_id
                        LEFT OUTER JOIN track_ext
                        ON track.d_release_id = track_ext.d_release_id
                        AND track.d_track_no = track_ext.d_track_no'''
        return self._select_simple(['track.d_release_id','discogs_id',
          'discogs_title', 'd_catno', 'track.d_artist', 'track.d_track_name',
          'track.d_track_no', 'track_ext.m_rec_id_override'],
           tables, condition=where, fetchone=True, orderby='release.discogs_id')
           
    def upsert_track_ext(self, orig, edit_answers):
        track_no = orig['d_track_no'].upper()  # always save uppercase track numbers
        release_id = orig['d_release_id']

        fields_ins = ''
        fields_ins_vals = ''
        fields_upd = ''
        values_list = []
        for key, answer in edit_answers.items():
            log.debug('key: {}, value: {}'.format(key, answer))
            # update fields key = ? snippets
            if fields_upd == '':
                fields_upd += "{} = ? ".format(key)
            else:
                fields_upd += ", {} = ? ".format(key)
            # insert fields (keys) and values (list of ?)
            fields_ins += ", {}".format(key)
            fields_ins_vals += ", ?"
            values_list.append(answer)

        if len(edit_answers) == 0:  # only update if necessary
            return True

        try:
            sql_i='''INSERT INTO track_ext(d_release_id, d_track_no{})
                        VALUES(?, ?{});'''.format(fields_ins, fields_ins_vals)
            tuple_i = (release_id, track_no) + tuple(values_list)
            return self.execute_sql(sql_i, tuple_i, raise_err=True)
        except sqlerr as e:
            if "UNIQUE constraint failed" in e.args[0]:
                log.debug("Track already in DiscoBASE (track_ext), updating ...")
                try:
                    sql_u='''
                     UPDATE track_ext SET {}
                       WHERE d_release_id = ? AND d_track_no = ?;'''.format(
                           fields_upd)
                    tuple_u = tuple(values_list) + (release_id, track_no)
                    return self.execute_sql(sql_u, tuple_u, raise_err=True)
                except sqlerr as e:
                    log.error("MODEL: upsert_track_ext: %s", e.args[0])
                    return False
            else:
                log.error("MODEL: %s", e.args[0])
                return False


class Brainz (object):

    def __init__(self, musicbrainz_user, musicbrainz_pass, musicbrainz_appid):
        self.ONLINE = False
        self.musicbrainz_user = musicbrainz_user
        self.musicbrainz_password = musicbrainz_pass
        self.musicbrainz_appid = musicbrainz_appid
        if self.musicbrainz_connect(musicbrainz_user, musicbrainz_pass, musicbrainz_appid):
            self.ONLINE = True
            log.info("MODEL: Brainz class is ONLINE.")

    # musicbrainz connect try,except wrapper
    def musicbrainz_connect(self, mb_user, mb_pass, mb_appid):
        # If you plan to submit data, authenticate
        m.auth(mb_user, mb_pass)
        m.set_useragent(mb_appid[0], mb_appid[1])  # 0=version, 1=app
        # If you are connecting to a different server
        # m.set_hostname("beta.musicbrainz.org")
        # m.set_rate_limit(limit_or_interval=1.0, new_requests=1)
        try:  # test request
            m.get_artist_by_id("952a4205-023d-4235-897c-6fdb6f58dfaa", [])
            self.ONLINE = True
            return True
        except WebServiceError as exc:
            log.error("connecting to MusicBrainz: %s" % exc)
            self.ONLINE = False
            return False

    def get_mb_artist_by_id(self, mb_id):
        try:
            return m.get_artist_by_id(mb_id, [])
        except WebServiceError as exc:
            log.error("requesting data from MusicBrainz: %s (WebServiceError)" % exc)
            log.debug("MODELS: get_mb_artist_by_id returns False.")
            return False
        except Exception as exc:
            log.error("requesting data from MusicBrainz: %s (Exception)" % exc)
            log.debug("MODELS: get_mb_artist_by_id returns empty dict.")
            return {}

    def search_mb_releases(self, artist, album, cat_no=False,
          limit = 10, strict = False):
        try:
            if cat_no:
                return m.search_releases(artist=artist, release=album,
                    catno = cat_no, limit=limit, strict=strict)
            else:
                return m.search_releases(artist=artist, release=album,
                    limit=limit, strict=strict)
        except WebServiceError as exc:
            log.error("requesting data from MusicBrainz: %s (WebServiceError)" % exc)
            log.debug("MODELS: search_mb_releases returns False.")
            return False
        except Exception as exc:
            log.error("requesting data from MusicBrainz: %s (Exception)" % exc)
            log.debug("MODELS: search_mb_releases returns empty dict.")
            return {}

    def get_mb_release_by_id(self, mb_id):
        try:
            return m.get_release_by_id(mb_id, includes=["release-groups",
            "artists", "labels", "url-rels", "recordings",
            "recording-rels", "recording-level-rels" ])
        except WebServiceError as websvcerr:
            log.error("requesting data from MusicBrainz: %s (WebServiceError)" % websvcerr)
            log.debug("MODELS: get_mb_release_by_id returns empty dict.")
            return {}
        except Exception as exc:
            log.error("requesting data from MusicBrainz: %s (Exception)" % exc)
            log.debug("MODELS: get_mb_release_by_id returns empty dict.")
            return {}

    def get_mb_recording_by_id(self, mb_id):
        try:
            return m.get_recording_by_id(mb_id, includes=[
             "url-rels"
            ])
        except WebServiceError as exc:
            log.error("requesting data from MusicBrainz: %s (WebServiceError)" % exc)
            log.debug("MODELS: get_mb_recording_by_id returns False.")
            return False
        except Exception as exc:
            log.error("requesting data from MusicBrainz: %s (Exception)" % exc)
            log.debug("MODELS: get_mb_recording_by_id returns empty dict.")
            return {}

    def get_urls_from_mb_release(self, full_rel):  # takes what get_mb_release_by_id returned
        # log.debug(full_rel['release'].keys())
        if 'url-relation-list' in full_rel['release']:
            return full_rel['release']['url-relation-list']
        else:
            return []

    def get_catno_from_mb_label(self, mb_label):  # label-info-list item
        # log.debug(mb_label)
        if 'catalog-number' in mb_label:
            return mb_label['catalog-number']
        else:
            return ''

    def _get_accousticbrainz(self, urlpart):
        headers={'Accept': 'application/json' }
        url="https://acousticbrainz.org/api/v1/{}".format(urlpart)
        try:
            resp = requests.get(url, headers=headers, timeout=7)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            log.debug("fetching AcousticBrainz MBID: %s (HTTPError)", errh)
            if "Not found" in errh.response.text:
                log.warning("AcousticBrainz doesn't have this recording yet. Consider submitting it!")
            return None
        except requests.exceptions.ConnectionError as errc:
            log.error("fetching AcousticBrainz MBID: %s (ConnectionError)", errc)
            return None
        except requests.exceptions.Timeout as errt:
            log.error("fetching AcousticBrainz MBID: %s (Timeout)", errt)
            return None
        except requests.exceptions.RequestException as erre:
            log.error("fetching AcousticBrainz MBID: %s (RequestException)", erre)
            return None

        if resp.ok:
            _json = json.loads(resp.content)
            return _json
        else:
            log.debug("No valid AcousticBrainz response. Returning None.")
            return None


    def _get_accbr_low_level(self, mb_id):
        low_level = self._get_accousticbrainz("{}/low-level".format(mb_id))
        # pprint.pprint(low_level)
        return low_level

    def _get_accbr_high_level(self, mb_id):
        return self._get_accousticbrainz("{}/high-level".format(mb_id))

    # def _get_accbr_url_rels(self, )

    def get_accbr_bpm(self, mb_id):
        try:
            ab_return = self._get_accbr_low_level(mb_id)
            return ab_return['rhythm']['bpm']
        except:
            return None

    def get_accbr_key(self, mb_id):
        try:
            ab_return = self._get_accbr_low_level(mb_id)
            if ab_return['tonal']['key_scale'] == 'minor':
                majmin = 'm'
            else:
                majmin = ''
            key_key = '{}{}'.format(ab_return['tonal']['key_key'], majmin)
            return key_key
        except:
            return None

    def get_accbr_chords_key(self, mb_id):
        try:
            ab_return = self._get_accbr_low_level(mb_id)
            if ab_return['tonal']['chords_scale'] == 'minor':
                majmin = 'm'
            else:
                majmin = ''
            chords_key = '{}{}'.format(ab_return['tonal']['chords_key'], majmin)
            return chords_key
        except:
            return None


class Brainz_match (Brainz):  # we are based on Brainz, but it's not online
    '''This class tries to match _one_ given release and/or recording with
        musicbrainz using the information passed in init'''

    def __init__(self, mb_user, mb_pass, mb_appid,
          d_release_id, d_release_title, d_catno, d_artist, d_track_name,
          d_track_no, d_track_no_num,
          detail = 1):
        # FIXME we take mb credentials from passed coll_ctrl object
        super().__init__(mb_user, mb_pass, mb_appid)
        # we don't need to create a Brainz obj, we are a child of it
        # remember all original discogs names
        self.d_release_id_orig = d_release_id
        self.d_release_title_orig = d_release_title
        self.d_catno_orig = d_catno
        self.d_artist_orig = d_artist
        self.d_track_name_orig = d_track_name
        self.d_track_no_orig = d_track_no
        self.d_track_no_num_orig = d_track_no_num
        # self.detail = detail
        # match methods and times init
        self.release_match_method = ''
        self.release_mbid = ''
        self.rec_match_method = ''
        self.rec_mbid = ''
        # strip and lowercase here already, we need it all the time
        self.d_release_id = d_release_id  # no mods here, just streamlining
        self.d_release_title = d_release_title.lower()
        # self.d_catno = d_catno.upper().replace(' ', '') # exp. with upper here
        self.d_catno = d_catno.upper().replace(' ', '')
        if d_artist:
            self.d_artist = d_artist.lower()
        else:  # if it's None or something else
            self.d_artist = ''
        self.d_track_name = d_track_name.lower()
        self.d_track_no = d_track_no.upper()  # upper comparision everywhere
        self.d_track_no_num = int(d_track_no_num)

    def fetch_mb_releases(self, detail):  # fetching controllable from outside
        # decide which search method is used according to detail (-z count)
        # FIXME error handling should be happening here
        if detail < 2:  # be strict, also use _original_ data here
            log.debug('strict catno: {}'.format(self.d_catno_orig))
            log.debug('strict artist: {}'.format(self.d_artist_orig))
            log.debug('strict release: {}'.format(self.d_release_title_orig))
            self.mb_releases = self.search_mb_releases(
                self.d_artist_orig, self.d_release_title_orig,
                self.d_catno_orig, limit = 5, strict = True)
        else:  # fuzzy search
            self.mb_releases = self.search_mb_releases(
                self.d_artist, self.d_release_title, self.d_catno,
                  limit = 5, strict = False)
        return True  # FIXME error handling

    def fetch_mb_matched_rel(self, rel_mbid = False): # mbid passable from outside
        if rel_mbid: # given from outside, rest of necess. data from init
            self.mb_matched_rel = self.get_mb_release_by_id(rel_mbid)
        else: # we have it as class attribute already
            self.mb_matched_rel = self.get_mb_release_by_id(self.release_mbid)
        return True # FIXME error handling

    def match_release(self): # start a match run (multiple things are tried)
        # first url-match
        self.release_mbid = self.url_match()
        # and then catno-match
        if not self.release_mbid:
            self.release_mbid = self.catno_match()
        # and now try again with some name variation tricks
        # sometimes digital releases have additional D at end or in between
        if not self.release_mbid:
            self.release_mbid = self.catno_match(variations = True)
        # if we still didn't find anything, we have logged already and are
        # returning empty string here
        return self.release_mbid

    def match_recording(self): # start a match run (multiple things are tried)
        #pprint.pprint(matched_rel) # human readable json
        # get track position as a number from discogs release
        #print(d_rel.tracklist[index])
        #d_track_position = d_rel.tracklist[index]
        rec_mbid = self.track_name_match()
        if not rec_mbid:
            rec_mbid = self.track_no_match()
        return rec_mbid # if we didn't find, we logged already and return ''

    # define matching methods as in update_track.... here
    def url_match(self):
        '''finds Release MBID by looking through Discogs links.'''
        # reset match method var. FIXME is this the right place
        self.release_match_method = ''
        for release in self.mb_releases['release-list']:
            log.info('CTRL: ...Discogs-URL-matching MB-Release:')
            log.info('CTRL: ..."{}"'.format(release['title']))
            full_mb_rel = self.get_mb_release_by_id(release['id'])
            #pprint.pprint(full_mb_rel) # DEBUG
            urls = self.get_urls_from_mb_release(full_mb_rel)
            if urls:
                for url in urls:
                    if url['type'] == 'discogs':
                        log.info('CTRL: ...trying Discogs URL: ..{}'.format(
                            url['target'].replace('https://www.discogs.com/', '')))
                        if str(self.d_release_id) in url['target']:
                            log.info(
                              'CTRL: Found MusicBrainz match (via Discogs URL)')
                            _mb_rel_id = release['id']
                            self.release_match_method = 'Discogs URL'
                            return _mb_rel_id # found release match
        return False

    def catno_match(self, variations = False):
        '''finds Release MBID by looking through catalog numbers.'''
        # reset match method var. FIXME is this the right place
        self.release_match_method = ''
        for release in self.mb_releases['release-list']:
            #_mb_rel_id = False # this is what we are looking for
            if variations:
                log.info('CTRL: ...CatNo-matching (variations) MB-Release:')
                log.info('CTRL: ..."{}"'.format(release['title']))
            else:
                log.info('CTRL: ...CatNo-matching (exact) MB-Release:')
                log.info('CTRL: ..."{}"'.format(release['title']))
            full_rel = self.get_mb_release_by_id(release['id'])
            # FIXME should we do something here if full_rel not successful?

            for mb_label_item in full_rel['release']['label-info-list']:
                mb_catno_orig = self.get_catno_from_mb_label(mb_label_item)
                mb_catno = mb_catno_orig.upper().replace(' ', '')
                #log.debug(
                #  'CTRL: ...MB CatNo (upper, no-ws): {}'.format(mb_catno))

                if variations == False: # this is the vanilla exact-match
                    log.info('CTRL: ...DC CatNo: {}'.format(self.d_catno_orig))
                    log.info('CTRL: ...MB CatNo: {}'.format(mb_catno_orig))
                    if mb_catno == self.d_catno:
                        self.release_match_method = 'CatNo (exact)'
                        self._catno_match_found_msg()
                        return release['id']

                else: # these are the variation matches
                    # log original DC CatNo only once
                    log.info('CTRL: ...DC CatNo: {}'.format(self.d_catno_orig))

                    # start with simple "ending differences"
                    log.info('CTRL: ...MB CatNo: {} (CD cut off)'.format(mb_catno_orig))
                    mb_catno_last2 = mb_catno[-2:]
                    if mb_catno_last2 == 'CD':
                        mb_catno_cd_cut = mb_catno[:-2]
                        if mb_catno_cd_cut == self.d_catno:
                            self.release_match_method = 'CatNo (var 3)'
                            self.release_mbid = release['id']
                            self._catno_match_found_msg()
                            return self.release_mbid

                    log.info('CTRL: ...MB CatNo: {} (D cut off)'.format(mb_catno_orig))
                    mb_catno_last1 = mb_catno[-1:]
                    if mb_catno_last1 == 'D':
                        mb_catno_d_cut = mb_catno[:-1]
                        if mb_catno_d_cut == self.d_catno:
                            self.release_match_method = 'CatNo (var 1)'
                            self.release_mbid = release['id']
                            self._catno_match_found_msg()
                            return self.release_mbid

                    # now the trickier stuff - char in between is different
                    log.info('CTRL: ...MB CatNo: {} (middle cut out)'.format(
                      mb_catno_orig))
                    # FIXME extendable via config.yaml
                    middle_terms = ['-', '#', 'D', 'CD', 'BLACK']
                    if self._catno_has_numtail(mb_catno):
                        for term in middle_terms:
                            log.info('CTRL: ...trying split at: {}'.format(term))
                            parts = self._catno_cutter(mb_catno, term)
                            if parts['term'] == term:
                                mb_catno_d_betw_cut = '{}{}'.format(
                                      parts['before'], parts['after'])
                                if mb_catno_d_betw_cut == self.d_catno:
                                    self.release_match_method = 'CatNo (var 2)'
                                    self.release_mbid = release['id']
                                    self._catno_match_found_msg()
                                    return self.release_mbid

                    # we didn't find a variation and return False
                    log.info('CTRL: ...no applicable variations found')
                    return False

    def _catno_has_numtail(self, catno):
        numtail = re.split('[^\d]', catno)[-1]
        log.debug('CTRL: ...catno_match_numtail return: {}'.format(numtail))
        return numtail

    def _catno_cutter(self, catno, term):
        '''returns 3 parts of catno: before delimiter-term, the delim-term
           and after delim-term, which _has_ to be a number'''
        ret_dict = {}
        # first thing: the tail is a number check, exit if not
        numtail = re.split('[^\d]', catno)[-1]
        if not numtail:
            return False # should never happen, we catch it with _catno_has_numtail
        # before delimiter-term check
        beforenum = re.split('[^\D]', catno)[0]
        #log.debug('CTRL: ...catno_cutter: beforenum {}'.format(beforenum))
        split_at_term = beforenum.split(term)
        #log.debug('CTRL: ...catno_cutter: split_at_term {}'.format(split_at_term))
        ret_dict['before'] = split_at_term[0]
        ret_dict['term'] = term
        ret_dict['after'] = numtail
        log.debug('CTRL: ...catno_cutter: before: {}'.format(ret_dict['before']))
        #log.debug('CTRL: ...catno_cutter: term: {}'.format(ret_dict['term']))
        log.debug('CTRL: ...catno_cutter: after: {}'.format(ret_dict['after']))
        return ret_dict

    def _catno_match_found_msg(self):
        # only show this final log line if we found a match
        log.info(
          'CTRL: Found MusicBrainz release match via {} '.format(
              self.release_match_method))

    def track_name_match(self):
        #pprint.pprint(_mb_release) # human readable json
        self.rec_match_method = ''
        for medium in self.mb_matched_rel['release']['medium-list']:
            for track in medium['track-list']:
                _rec_title = track['recording']['title']
                _rec_title_low = _rec_title.lower() # we made discogs lower too
                if _rec_title_low == self.d_track_name:
                    self.rec_mbid = track['recording']['id']
                    log.info('CTRL: Track name matches: {}'.format(
                        _rec_title))
                    log.info('CTRL: Recording MBID: {}'.format(
                        self.rec_mbid)) # finally we have a rec MBID
                    self.rec_match_method = 'Track Name'
                    return self.rec_mbid
        log.info('CTRL: No track name match: {} vs. {}'.format(
            self.d_track_name_orig, _rec_title))
        return False

    def track_no_match(self):
        #pprint.pprint(_mb_release) # human readable json
        self.rec_match_method = ''
        for medium in self.mb_matched_rel['release']['medium-list']:
            #track_count = len(medium['track-list'])
            for track in medium['track-list']:
                _rec_title = track['recording']['title']
                track_number = track['number'].upper(), # could be A, AA, a, ..
                track_position = int(track['position']) # starts at 1, ensure int
                if track_number == self.d_track_no:
                    self.rec_mbid = track['recording']['id']
                    log.info('CTRL: Track number matches: {}'.format(
                        _rec_title))
                    log.info('CTRL: Recording MBID: {}'.format(
                        self.rec_mbid)) # finally we have a rec MBID
                    self.rec_match_method = 'Track No'
                    return self.rec_mbid
                elif track_position == self.d_track_no_num:
                    self.rec_mbid = track['recording']['id']
                    log.info('CTRL: Track number "numerical" matches: {}'.format(
                        _rec_title))
                    log.info('CTRL: Recording MBID: {}'.format(
                        self.rec_mbid)) # finally we have a rec MBID
                    self.rec_match_method = 'Track No (num)'
                    return self.rec_mbid
        log.info('CTRL: No track number or numerical position match: {} vs. {}'.format(
            self.d_track_no_num, track_position))
        return False

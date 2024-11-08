import logging
# import pprint

from discodos.model.database import Database
from discodos.utils import is_number  # most of this should only be in view

log = logging.getLogger('discodos')


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
        return self._select_simple(
            ['MAX(track_pos)'], 'mix_track',
            condition="mix_id = {}".format(self.id), fetchone=True
        )

    def get_tracks_of_one_mix(self, start_pos=False):
        log.info("MODEL: Getting tracks of a mix, from mix_track_table only)")
        if not start_pos:
            where = "mix_id == {}".format(self.id)
        else:
            where = "mix_id == {} and track_pos >= {}".format(self.id, start_pos)
        return self._select_simple(
            ['*'], 'mix_track', where, fetchone=False, orderby='track_pos'
        )

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
        return self._select_simple(
            ['track_pos', 'mix_track.d_release_id',
             'discogs_id', 'discogs_title', 'd_catno', 'track.d_artist',
             'd_track_name', 'mix_track.d_track_no', 'm_rec_id_override'],
            tables, where, fetchone=False, orderby='mix_track.track_pos'
        )

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
        return self._select_simple(
            ['track_pos', 'mix_track.d_release_id',
             'discogs_id', 'discogs_title', 'd_catno', 'track.d_artist',
             'd_track_name', 'mix_track.d_track_no', 'm_rec_id_override'],
            tables, fetchone=False, distinct=True, offset=offset,
            orderby='mix_track.mix_id, mix_track.track_pos'
        )

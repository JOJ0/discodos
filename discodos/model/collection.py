import logging
from sqlite3 import Error as sqlerr

from discodos.model.discogs import DiscogsMixin
from discodos.model.database import Database
from discodos.utils import (
    is_number, timestamp_now
)

log = logging.getLogger('discodos')


class Collection (Database, DiscogsMixin):  # pylint: disable=too-many-public-methods
    """Offline record collection class."""
    def __init__(self, db_conn, db_file=False):
        super().__init__(db_conn, db_file)
        self.d = False
        self.me = False
        self.ONLINE = False # set True by discogs_connect method

    # Base fetchers and inserts

    def get_all_db_releases(self, orderby='d_artist, discogs_title', as_dict=False):
        return self._select_simple(
            [
                "d_catno",
                "d_artist",
                "discogs_title",
                "discogs_id",
                "m_rel_id",
                "m_rel_id_override",
            ],
            "release",
            as_dict=as_dict,
            orderby=orderby,
        )

    def get_track(self, release_id, track_no):
        log.info("MODEL: Returning collection track {} from release {}.".format(
            track_no, release_id))
        where = 'track.d_release_id == {} AND track.d_track_no == "{}"'.format(
            release_id, track_no.upper())  # we always save track_nos uppercase
        join = '''track LEFT OUTER JOIN track_ext
                    ON track.d_release_id = track_ext.d_release_id
                    AND track.d_track_no = track_ext.d_track_no'''
        return self._select_simple(
            ['track.d_track_no', 'track.d_release_id',
             'd_track_name', 'key', 'key_notes', 'bpm', 'notes', 'm_rec_id_override',
             'a_key', 'a_chords_key', 'a_bpm'],
            join, fetchone=True, condition=where
        )

    def search_release_offline(self, id_or_title):
        if is_number(id_or_title):
            try:
                return self.get_release_by_id(id_or_title)
            except Exception as Exc:
                log.error("Not found or Database Exception: %s\n", Exc)
                raise Exc
        else:
            try:
                releases = self._select_simple(
                    ['*'], 'release',
                    'discogs_title LIKE "%{}%" OR d_artist LIKE "%{}%"'.format(
                        id_or_title, id_or_title),
                    fetchone=False, orderby='d_artist'
                )
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
        fields = ['track.d_artist', 'track.d_track_name',
                  'release.d_catno', 'track.d_track_no',
                  'track.a_key', 'track.a_chords_key', 'track.a_bpm',
                  'track_ext.key', 'track_ext.bpm', 'track_ext.key_notes',
                  'track_ext.notes',
                  'release.discogs_id', 'release.discogs_title',
                  'release.import_timestamp', 'release.in_d_collection',
                  'track.m_rec_id', 'track_ext.m_rec_id_override',
                  'track.m_match_method AS recording_match_method',
                  'track.m_match_time AS recording_match_time',
                  'release.m_rel_id',
                  'release.m_match_method AS release_match_method',
                  'release.m_match_time AS release_match_time']
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

    def get_release_by_id(self, release_id):
        return self._select_simple(
            ["*"], "release", f"discogs_id == {release_id}", fetchone=True
        )

    def get_release_tracks_by_id(self, release_id):
        return self._select_simple(
            ["*"],
            "release",
            f"discogs_id == {release_id}",
            fetchone=False,
            join=[
                ("LEFT OUTER", "track", "discogs_id = track.d_release_id")
            ],
            as_dict=True
        )

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
                except sqlerr as ee:
                    log.error("MODEL: upsert_track: %s", ee.args[0])
                    return False
            else:
                log.error("MODEL: %s", e.args[0])
                return False

    def upsert_track_ext(self, orig, edit_answers):  # pylint: disable=too-many-locals
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
                log.debug(
                    "Track existing in track_ext table, updating ..."
                )
                try:
                    sql_u='''
                        UPDATE track_ext SET {}
                          WHERE d_release_id = ? AND d_track_no = ?;'''.format(
                        fields_upd)
                    tuple_u = tuple(values_list) + (release_id, track_no)
                    return self.execute_sql(sql_u, tuple_u, raise_err=True)
                except sqlerr as ee:
                    log.error("MODEL: upsert_track_ext: %s", ee.args[0])
                    return False
            else:
                log.error("MODEL: %s", e.args[0])
                return False

    # Release & collection items

    def get_all_collection_items(self):
        """Returns all entries of DiscoBASE collection table."""
        return self._select("SELECT * FROM collection", as_dict=True)

    def set_collection_item_orphaned(self, instance_id):
        """Sets orphaned flag on a DiscoBASE collection item."""
        return self.execute_sql(
            """
            UPDATE collection SET coll_orphaned = 1
                WHERE d_coll_instance_id == ?;
            """,
            (instance_id,),
        )

    def set_collection_item_folder(
        self, instance_id, folder_id, sold_folder_id, timestamp
    ):
        """Updates folder_id on a DiscoBASE collection item.

        If a valid sold_folder_id is passed the item will be marked as sold.
        """
        sold = 0
        if is_number(sold_folder_id):
            sold = folder_id == int(sold_folder_id)
        return self.execute_sql(
            """
            UPDATE collection
            SET d_coll_folder_id = ?, coll_sold = ?, coll_orphaned = 0, coll_mtime = ?
                WHERE d_coll_instance_id == ?;
            """,
            (folder_id, sold, timestamp, instance_id)
        )

    def create_release(
        self, release_id, release_title, release_artists, d_catno
    ):  # pylint: disable=too-many-arguments,too-many-positional-arguments
        """Creates a release entry, returns False on errors, last_row_id on success.

        Success is either newly-created or existing-updated.
        """
        try:
            insert_sql = """
                INSERT OR FAIL INTO release
                    (discogs_id, discogs_title, import_timestamp, d_artist, d_catno)
                    VALUES (?, ?, ?, ?, ?)
            """
            in_tuple = (
                release_id,
                release_title,
                timestamp_now(),
                release_artists,
                d_catno,
            )
            return self.execute_sql(insert_sql, in_tuple, raise_err=True)
        except sqlerr as e:
            if not "UNIQUE constraint failed" in e.args[0]:
                log.error("MODEL: create_release (new) %s", e.args[0])
                return False

            log.debug("MODEL: Release already in DiscoBASE, updating ...")
            try:
                upd_sql = """
                    UPDATE release SET
                    (discogs_title, import_timestamp, d_artist, d_catno) = (?, ?, ?, ?)
                    WHERE discogs_id == ?;
                """
                upd_tuple = (
                    release_title,
                    timestamp_now(),
                    release_artists,
                    d_catno,
                    release_id,
                )
                return self.execute_sql(upd_sql, upd_tuple, raise_err=True)
            except sqlerr as ee:
                log.error("MODEL: create_release (update): %s", ee.args[0])
                return False

    def delete_release(self, release_id):
        """Deletes a release from DiscoBASE"""
        in_db = self._select_simple(
            ["discogs_id"], "release", condition=f"discogs_id == {release_id}"
        )
        if not in_db:
            log.warning("Release not in DiscoBASE.")
            return None
        return self.execute_sql(
            "DELETE FROM release WHERE discogs_id == ?", (release_id, )
        )

    def create_collfolders(self, folders):
        """Creates/updates collection folders in DiscoBASE collfolder table.

        Expects a list of dicts with DiscoBASE field names already.
        Returns a bool on errors, a lastrowid integer on success.
        """
        fields = ", ".join(folders[0].keys())  # Use first folder for field names
        placeholders = ", ".join("?" for _ in folders[0])
        update_fields = ", ".join(
            f"{key} = excluded.{key}" for key in folders[0] if key != "d_collfolder_id"
        )

        try:
            for folder in folders:
                values = tuple(folder.values())  # Single row insert
                self.execute_sql(
                    f"""INSERT INTO collfolder ({fields}) VALUES ({placeholders})
                    ON CONFLICT(d_collfolder_id) DO UPDATE SET {update_fields}""",
                    values,
                    raise_err=True,
                )
            return True
        except sqlerr as e:
            log.error("MODEL: create_collfolder: %s", e.args[0])
            return False

    def get_folder_name_by_id(self, folder_id):
        """Currently unused."""
        folder_row = self._select_simple(
            ["d_collfolder_name"],
            "collfolder",
            condition=f"d_collfolder_id == {folder_id}",
            fetchone=True
        )
        if folder_row:
            return folder_row["d_collfolder_name"]
        return folder_id

    def get_folder_id_by_name(self, folder_name):
        """Get collection item's folder id by its name.

        Returns None if not found.
        """
        folder_row = self._select_simple(
            ["d_collfolder_id"],
            "collfolder",
            condition=f'd_collfolder_name == "{folder_name}"',
            fetchone=True
        )
        if folder_row:
            return folder_row["d_collfolder_id"]
        return None

    def get_collection_folders(self):
        """Get a list of dicts for all collection folders."""
        folder_rows = self._select_simple(
            ["*"],
            "collfolder",
            orderby="d_collfolder_name ASC",
            as_dict=True,
        )
        return folder_rows

    # Get by release. Cleanup helpers.

    def get_collection_items_by_release(self, release_id, quiet=False):
        """Gets all collection item instances via a release_id from DiscoBASE"""
        in_db = self._select_simple(
            ["*"],
            "collection",
            condition=f"d_coll_release_id == {release_id} and NOT coll_orphaned",
            as_dict=True,
        )
        if not in_db and not quiet:
            log.warning(
                f"No instance of release {release_id} found in DiscoBASE collection."
            )
            return []
        return in_db

    def get_sales_listings_by_release(self, release_id, quiet=False):
        """Gets all sales listing via a release_id from DiscoBASE"""
        in_db = self._select_simple(
            ["*"],
            "sales",
            condition=f"d_sales_release_id == {release_id}",
            as_dict=True,
        )
        if not in_db and not quiet:
            log.warning(
                f"No sales listing of release {release_id} found in DiscoBASE."
            )
            return []
        return in_db

    def get_mix_tracks_by_release(self, release_id, quiet=False):
        """Gets all mix_tracks via a release_id from DiscoBASE"""
        in_db = self._select_simple(
            ["*"],
            "mix_track",
            condition=f"d_release_id == {release_id}",
            as_dict=True,
        )
        if not in_db and not quiet:
            log.warning(
                f"No mixed track on release {release_id} found in DiscoBASE."
            )
            return []
        return in_db

    def delete_collection_item(self, instance_id):
        """Deletes a collection item instance from DiscoBASE."""
        in_db = self._select_simple(
            ["d_coll_instance_id"],
            "collection",
            condition=f"d_coll_instance_id == {instance_id}",
        )
        if not in_db:
            log.warning("Collection item instance not in DiscoBASE.")
            return None
        return self.execute_sql(
            "DELETE FROM collection WHERE d_coll_instance_id == ?", (instance_id, )
        )

    def create_collection_item(self, instance):
        """Creates a single entry to collection table and ensures up to date data.

        Expects a collection item instance as a dictionary with keys named like
        DiscoBASE fields.

        Returns a bool on errors, a lastrowid integer on success.

        """
        # join together a comma delim string for the SQL statement
        keys_str = ', '.join(instance.keys())
        # generate a tuple version of the values
        values = tuple(instance.values())
        values_placeholders = ', '.join(['?'] * len(instance))
        # Prepare update fields (we want to update all columns except the
        # primary keys on conflict)
        update_fields = ', '.join([
            f"{key} = excluded.{key}"
            for key in instance.keys()
            if key not in {"d_coll_instance_id"}
        ])

        try:
            insert_sql = f"""
            INSERT INTO collection ({keys_str}) VALUES ({values_placeholders})
            ON CONFLICT(d_coll_instance_id) DO UPDATE SET
                {update_fields}
            """
            return self.execute_sql(insert_sql, values, raise_err=True)
        except sqlerr as e:
            if e.sqlite_errorname == "SQLITE_CONSTRAINT_TRIGGER":
                log.info("MODEL: create_collection_item: %s", e.args[0])
                return False
            log.error("MODEL: create_collection_item: %s", e.args[0])
            return False

    # Suggest fetchers

    def track_report_snippet(self, track_pos, mix_id):
        track_pos_before = track_pos - 1
        track_pos_after = track_pos + 1
        sql_sel = '''
            SELECT track_pos, discogs_title, track.d_artist, d_track_name,
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
            track_pos, track_pos_before, track_pos_after, mix_id
        )
        tracks_snippet = self._select(sql_sel, fetchone=False)
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
            'd_release_id == "{}" AND d_track_no == "{}"'.format(
                release_id, track_no.upper()
            )
        )
        log.info("MODEL: Returning track_report_occurences data.")
        return occurences_data

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
            ORDER BY chosen_key, chosen_bpm'''.format(
            min_bpm, max_bpm, min_bpm, max_bpm, key)
        return self._select(sql_bpm, fetchone=False)

    # Stats fetchers

    def stats_match_method_release(self):
        sql_stats = '''
                    SELECT m_match_method, COUNT(*) FROM release GROUP BY m_match_method;
                    '''
        return self._select(sql_stats, fetchone=False)

    def stats_releases_total(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM release;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_tracks_total(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM track;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_tracks_total_ext(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM track_ext;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_track_ext_orphaned(self):
        '''Checks for orphaned rows in track_ext table.

        track_ext saves user provided info about tracks: key, bpm, notes, ...

        There is currently no job that would cleanup such a row if it is not
        used anymore, e.g all above mentioned user provided info was deleted.

        For now this is just a maintenance check-tool to keep track of this
        issue.
        '''
        sql_stats = '''
                    SELECT COUNT(*) FROM track_ext WHERE
                        key IS NULL
                        AND key_notes IS NULL
                        AND bpm IS NULL
                        AND notes IS NULL
                        AND m_rec_id_override IS NULL
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_releases_matched(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM release WHERE m_match_time IS NOT NULL;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_tracks_matched(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM track WHERE m_match_time IS NOT NULL;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_collection_items_discobase(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM release LEFT OUTER JOIN collection
                    ON discogs_id = d_coll_release_id
                    WHERE coll_orphaned = 0;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_sales_listings_discobase(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM sales;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_sales_listings_forsale(self):
        sql_stats = """ SELECT COUNT(*) FROM sales
            WHERE d_sales_status = "forsale" OR d_sales_status = "expired";
            """
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_sales_listings_sold(self):
        sql_stats = '''
            SELECT COUNT(*) FROM sales WHERE d_sales_status = "sold";
            '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_mixtracks_total(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM mix_track;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_mixtracks_unique(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM (
                        SELECT DISTINCT d_release_id, d_track_no
                        FROM mix_track
                    );
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_tracks_key_brainz(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM track WHERE a_key IS NOT NULL;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_tracks_key_manual(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM track_ext WHERE key IS NOT NULL;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_tracks_bpm_brainz(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM track WHERE a_bpm IS NOT NULL;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_tracks_bpm_manual(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM track_ext WHERE bpm IS NOT NULL;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    # Brainz fetchers and inserts

    def get_all_tracks_for_brainz_update(self, offset=0, really_all=False,
                                         skip_unmatched=False):
        log.info("MODEL: Getting tracks. Preparing *Brainz mass update.")
        if offset > 0:
            offset = offset - 1
            log.info("MODEL: Subtracted 1 from offset (--resume 1 should "
                     "not alter anything).")
        where = '(a_key IS NULL or a_bpm IS NULL)' if not really_all else ''
        where += ' AND' if skip_unmatched and not really_all else ''
        where += ' m_rec_id IS NOT NULL' if skip_unmatched else ''
        tables = '''release
                      LEFT OUTER JOIN track
                      ON release.discogs_id = track.d_release_id
                        LEFT OUTER JOIN track_ext
                        ON track.d_release_id = track_ext.d_release_id
                        AND track.d_track_no = track_ext.d_track_no'''
        return self._select_simple([
            'release.discogs_id', 'track.d_release_id', 'discogs_title',
            'd_catno', 'track.d_artist', 'track.d_track_name',
            'track.d_track_no', 'track_ext.m_rec_id_override'],
            tables, condition=where,
            fetchone=False, orderby='release.discogs_id', offset=offset
        )

    def get_track_for_brainz_update(self, rel_id, track_no):
        log.info("MODEL: Getting track. Preparing *Brainz update.")
        where = 'track.d_release_id == {} AND track.d_track_no == "{}"'.format(
            rel_id, track_no)
        tables = '''release
                      LEFT OUTER JOIN track
                      ON release.discogs_id = track.d_release_id
                        LEFT OUTER JOIN track_ext
                        ON track.d_release_id = track_ext.d_release_id
                        AND track.d_track_no = track_ext.d_track_no'''
        return self._select_simple([
            'track.d_release_id', 'discogs_id',
            'discogs_title', 'd_catno', 'track.d_artist', 'track.d_track_name',
            'track.d_track_no', 'track_ext.m_rec_id_override'],
            tables, condition=where, fetchone=True,
            orderby='release.discogs_id'
        )

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

    # Key/value search

    def key_value_search_releases(
        self, search_key_value=None, orderby=None, filter_cols=None,
        custom_fields=None, reverse_order=False, sales_extra=False, limit=None,
    ):
        # filter_cols are defined in ViewCommon and passed via the controller call.
        replace_cols = filter_cols

        where = " AND ".join(
            [
                f'{replace_cols.get(k, k)} LIKE "%{v}%"'
                for k, v in search_key_value.items()
            ]
        )
        join = [
            ("LEFT OUTER", "sales", "discogs_id = sales.d_sales_release_id"),
            ("LEFT OUTER", "collection", "discogs_id = collection.d_coll_release_id"),
            ("LEFT OUTER", "collfolder", "d_coll_folder_id = d_collfolder_id"),
        ]
        if sales_extra:
            sold_field = "coll_sold as sold"
        else:
            sold_field = """
            CASE
                WHEN coll_sold = 1 OR sales_sold = 1 THEN 1
                ELSE 0
            END AS sold
            """
        fields = [
            "release.discogs_id",
            "release.d_catno",
            "release.d_artist",
            "release.discogs_title",
            """
            CASE
                WHEN coll_orphaned = 0 AND d_coll_instance_id > 0 THEN 1
                ELSE 0
            END AS in_c
            """,
            sold_field,
            "NULL AS d_sales_listing_id" if sales_extra else "d_sales_listing_id",
            "NULL AS d_sales_status" if sales_extra else "d_sales_status",
            "NULL AS d_sales_location" if sales_extra else "d_sales_location",
            "NULL AS d_sales_price" if sales_extra else "d_sales_price",
            "collection.d_coll_instance_id",
            "COALESCE(d_collfolder_name, d_coll_folder_id) AS d_collfolder_name",
            "collection.d_coll_notes",
            "collection.coll_mtime",
        ] if not custom_fields else custom_fields

        fields_union = [
            "sales.d_sales_release_id AS discogs_id",
            "release.d_catno",
            "release.d_artist",
            "release.discogs_title",
            "NULL AS in_c",
            "sales.sales_sold AS sold",
            "sales.d_sales_listing_id",
            "sales.d_sales_status",
            "sales.d_sales_location",
            "sales.d_sales_price",
            "NULL AS d_coll_instance_id",
            "NULL AS d_coll_folder_name",
            "NULL AS d_coll_notes",
            "NULL AS coll_mtime",
        ]
        union = [
            {
                "fields_list": fields_union,
                "table": "sales",
                "condition": f"{where}",
                "join": [
                    # also for now, exlcude JOIN with collection
                    # we potentially saved listing_id on sales import
                    # ("LEFT OUTER", "collection", "d_sales_listing_id = coll_d_sales_listing_id"),  # pylint: disable=line-too-long
                    ("LEFT OUTER", "release", "d_sales_release_id = discogs_id"),
                ],
            }
        ]

        rows = self._select_simple(
            fields,
            "release",
            fetchone=False,
            orderby=orderby,
            # exclude orphaned always, for now ...
            # above CASE statements currently redundant.
            condition=f"{where} AND coll_orphaned = 0",
            join=join,
            union=union if sales_extra else None,
            reverse_order=reverse_order,
            limit=limit,
        )
        return rows

    def get_one_release_for_list_app(
        self, release_id, orderby="d_artist, discogs_title"
    ):
        """Get one release with fields required for DiscodosListApp.

        Returns the same fields as key_value_search_release!
        """
        where = f"d_sales_release_id == {release_id}"
        join = [("LEFT", "sales", "discogs_id = d_sales_release_id")]

        rows = self._select_simple(
            [
                "discogs_id",
                "d_catno",
                "d_artist",
                "discogs_title",
                "in_d_collection",
                "d_sales_listing_id",
                "d_sales_status",
                "sold",
            ],
            "release", fetchone=False, orderby=orderby, condition=where, join=join,
        )
        return rows

    # Sales

    def create_sales_entry(self, listing_object):
        """Creates a single entry to sales table and ensures up to date data.

        Saves conditions and status as-is - in plain short key form (eg. VG+, forsale)
        """
        # join together a comma delim string for the SQL statement
        keys_str = ', '.join(listing_object.keys())
        # generate a tuple version of the values
        values = tuple(listing_object.values())
        values_placeholders = ', '.join(['?'] * len(listing_object))
        # Prepare update fields (we want to update all columns except the
        # primary keys on conflict)
        update_fields = ', '.join([
            f"{key} = excluded.{key}"
            for key in listing_object.keys()
            if key not in {"d_sales_listing_id"}
        ])

        try:
            insert_sql = f"""
            INSERT INTO sales ({keys_str}) VALUES ({values_placeholders})
            ON CONFLICT(d_sales_listing_id) DO UPDATE SET
                {update_fields}
            """
            return self.execute_sql(insert_sql, values, raise_err=True)
        except sqlerr as e:
            log.error("MODEL: create_sales_entry: %s", e.args[0])
            return False

    def get_sales_listing_details(self, listing_id, tui_view=False):
        """Get Marketplace listing details from DB if already imported.

        Always returns a dict, not Row.
        """
        if not listing_id:
            listing_id = "NULL"
        where = f"d_sales_listing_id == {listing_id}"

        tui_first =["d_sales_listing_id"]
        fields = [
            "d_sales_release_id",
            "d_sales_release_url",
            "d_sales_url",
            "d_sales_condition",
            "d_sales_sleeve_condition",
            "d_sales_comments",
            "d_sales_location",
            "d_sales_price",
            "d_sales_status",
            "d_sales_posted",
            "d_sales_allow_offers",
            "d_sales_comments_private",
            "d_sales_counts_as",
            "d_sales_weight",
        ]
        if tui_view:
            fields = tui_first + fields
            fields.remove("d_sales_release_id")
            fields.remove("d_sales_release_url")

        rows =  self._select_simple(
            fields,
            "sales",
            fetchone=True, condition=where, as_dict=True
        )
        return rows

    def toggle_collection_sold_flag(
        self, release_id, sold, instance_id=None, listing_id=None
    ):
        """Toggle sold flag on collection items.

        Expects boolean sold.

        Returns (True, last_row_id) on success or (False, release_info) on "error"

        Error state is: If multiple collection item instances we can't really decide
        which one to set sold. User must solve manually!

        If an instance_id was passed, decision is obvious, update sold flag and return
        early. If a listing_id was passed, it is also saved in the collection item
        record.
        """
        if instance_id and listing_id:
            log.info(
                f"MODEL: Set coll sold {sold}: instance {instance_id}, listing {listing_id}"
            )
            return True, self.execute_sql(
                """
                UPDATE collection SET
                    (coll_sold, coll_d_sales_listing_id) = (?, ?)
                    WHERE d_coll_instance_id == ?;
                """,
                (sold, instance_id, listing_id),
            )
        if instance_id:
            log.info(
                f"MODEL: Set coll sold {sold}: instance {instance_id}"
            )
            return (
                True,
                self.execute_sql(
                    """
                    UPDATE collection SET (coll_sold) = (?)
                    WHERE d_coll_instance_id == ?;
                    """,
                    (sold, instance_id),
                ),
            )

        # Solution is not entirely clear, fetch collection item instances and set only
        # if a single collection item is existing.
        instances = self._select_simple(
            ["d_coll_release_id", "d_coll_instance_id", "d_catno"],
            "collection",
            f"d_coll_release_id = {release_id}",
            join=[("LEFT", "release", "d_coll_release_id = discogs_id")],
            as_dict=True,
        )
        if len(instances) > 1:
            details = f"{instances[0]['d_coll_release_id']} {instances[0]['d_catno']}"
            log.info(
                "Multiple in collection. Mark sold manually: %s",
                details,
            )
            return False, details

        if listing_id:
            log.info(
                f"MODEL: Set coll sold {sold}: release {release_id}, listing_id {listing_id}"
            )
            return True, self.execute_sql(
                """
                UPDATE collection SET
                    (coll_sold, coll_d_sales_listing_id) = (?, ?)
                    WHERE d_coll_release_id == ?;
                """,
                (sold, listing_id, release_id),
            )
        # Fallback
        log.info(
            f"MODEL: Set coll sold {sold}: only release {release_id}"
        )
        return True, self.execute_sql(
            """
            UPDATE collection SET
                (coll_sold) = (?)
                WHERE d_coll_release_id == ?;
            """,
            (sold, release_id),
        )

    def get_sales_inventory(self, offset=0):
        """Get all Marketplace listing details from DB if already imported.

        Always returns a dict, not Row.
        """
        if offset > 0:
            offset = offset - 1
        rows =  self._select_simple(
            [
                "d_sales_listing_id",
                "d_sales_release_id",
                "d_sales_release_url",
                "d_sales_url",
                "d_sales_condition",
                "d_sales_sleeve_condition",
                "d_sales_price",
                "d_sales_comments",
                "d_sales_allow_offers",
                "d_sales_status",
                "d_sales_comments_private",
                "d_sales_counts_as",
                "d_sales_location",
                "d_sales_weight",
                "d_sales_posted",
            ],
            "sales",
            fetchone=False, condition=None, as_dict=True, offset=offset,
            orderby="d_sales_listing_id DESC"
        )
        return rows

    def delete_sales_inventory_item(self, listing_id):
        return self.execute_sql(
            "DELETE FROM sales WHERE d_sales_listing_id == ?", (listing_id,)
        )

    def stats_sales_items_total(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM sales;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

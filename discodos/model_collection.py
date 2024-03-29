from discodos.utils import is_number  # most of this should only be in view
import logging
# import pprint
import discogs_client
import discogs_client.exceptions
import requests.exceptions
import urllib3.exceptions
from sqlite3 import Error as sqlerr
import time
from datetime import datetime
import requests
from socket import gaierror

from discodos.model_database import Database

log = logging.getLogger('discodos')


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
                _appIdentifier, user_token=_userToken
            )
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
        return self._select_simple(
            ['d_catno', 'd_artist',
             'discogs_title', 'discogs_id', 'm_rel_id', 'm_rel_id_override'],
            'release', orderby='d_artist, discogs_title'
        )

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
                release.formats[0]['descriptions'][1]
            )

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
            if dbtrack is None:
                log.debug("MODEL: prepare_tracklist_info: Track not in DB. "
                          "Adding title/track_no only.")
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
        return self._select_simple(
            ['track.d_track_no', 'track.d_release_id',
             'd_track_name', 'key', 'key_notes', 'bpm', 'notes', 'm_rec_id_override',
             'a_key', 'a_chords_key', 'a_bpm'],
            join, fetchone=True, condition=where
        )

    def search_release_offline(self, id_or_title):
        if is_number(id_or_title):
            try:
                return self.search_release_id(id_or_title)
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
        return self._select_simple(
            ['*'], 'release',
            'discogs_id == {}'.format(release_id), fetchone=True
        )

    def create_release(self, release_id, release_title, release_artists, d_catno, d_coll=False):
        try:
            insert_sql = '''INSERT OR FAIL INTO release(discogs_id, discogs_title,
                                    import_timestamp, d_artist, in_d_collection, d_catno)
                                    VALUES(?, ?, ?, ?, ?, ?)'''
            in_tuple = (
                release_id, release_title,
                datetime.today().isoformat(' ', 'seconds'), release_artists,
                d_coll, d_catno
            )
            return self.execute_sql(insert_sql, in_tuple, raise_err=True)
        except sqlerr as e:
            if "UNIQUE constraint failed" in e.args[0]:
                log.debug("MODEL: Release already in DiscoBASE, updating ...")
                try:
                    upd_sql = '''UPDATE release SET (discogs_title,
                        import_timestamp, d_artist, in_d_collection, d_catno)
                        = (?, ?, ?, ?, ?) WHERE discogs_id == ?;'''
                    upd_tuple = (
                        release_title,
                        datetime.today().isoformat(' ', 'seconds'),
                        release_artists, d_coll, d_catno, release_id
                    )
                    return self.execute_sql(upd_sql, upd_tuple, raise_err=True)
                except sqlerr as e:
                    log.error("MODEL: create_release: %s", e.args[0])
                    return False
            else:
                log.error("MODEL: %s", e.args[0])
                return False

    def get_d_release(self, release_id, catch=True):
        try:
            r = self.d.release(release_id)
            if catch is True:
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
                "Discogs request rate limit is about to exceed, "
                "let's wait a little: %s",
                self.d._fetcher.rate_limit_remaining
            )
            # while int(self.d._fetcher.rate_limit_remaining) < remaining:
            time.sleep(sleep)
        else:
            log.info(
                "Discogs rate limit: %s remaining.",
                self.d._fetcher.rate_limit_remaining
            )

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
                        "MODEL: d_artists_parse: no artists in tracklist, "
                        "checking d_artists object..")
                    combined_name = self.d_artists_to_str(d_artists)
                    return combined_name
                else:
                    log.info("tr.artists len: {}".format(len(tr.artists)))
                    for a in tr.artists:
                        log.info("release.artists debug loop: {}".format(a.name))
                    combined_name = self.d_artists_to_str(tr.artists)
                    log.info(
                        "MODEL: d_artists_parse: several artists, "
                        "returning combined named {}".format(combined_name))
                    return combined_name
        log.debug('d_artists_parse: Track {} not existing on release.'.format(
            track_number))

    def d_tracklist_parse(self, d_tracklist, track_number):
        '''gets Track name from discogs tracklist object via track_number, eg. A1'''
        for tr in d_tracklist:
            # log.debug("d_tracklist_parse: this is the tr object: {}".format(dir(tr)))
            # log.debug("d_tracklist_parse: this is the tr object: {}".format(tr))
            if (track_number is not None
                    and tr.position.upper() == track_number.upper()):
                return tr.title
        log.debug(
            'd_tracklist_parse: Track {} not existing on release.'.format(
                track_number)
        )
        return False  # we didn't find the tracknumber

    def d_tracklist_parse_numerical(self, d_tracklist, track_number):
        '''get numerical track pos from discogs tracklist object via
           track_number, eg. A1'''
        for num, tr in enumerate(d_tracklist):
            if tr.position.lower() == track_number.lower():
                return num + 1  # return human readable (matches brainz position)
        log.debug("d_tracklist_parse_numerical: "
                  "Track {} not existing on release.".format(track_number))
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
            ORDER BY chosen_key, chosen_bpm'''.format(
            min_bpm, max_bpm, min_bpm, max_bpm, key)
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

    def stats_releases_d_collection_flag(self):
        sql_stats = '''
                    SELECT COUNT(*) FROM release WHERE in_d_collection == 1;
                    '''
        stats = self._select(sql_stats, fetchone=True)
        return stats[0] if stats else 0

    def stats_releases_d_collection_online(self):
        count = 0
        try:
            count = len(self.me.collection_folders[0].releases)
        except Exception as Exc:
            log.error("%s (Exception)", Exc)
        return count

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

    def d_get_first_catno(self, d_labels):
        '''get first found catalog number from discogs label object'''
        catno_str = ''
        if len(d_labels) == 0:
            log.warning("MODEL: Discogs release without Label/CatNo. "
                        "This is weird!")
        else:
            for cnt, label in enumerate(d_labels):
                if cnt == 0:
                    catno_str = label.data['catno']
                else:
                    log.warning('MODEL: Found multiple CatNos, '
                                'not adding "{}"'.format(label.data['catno']))
            log.info('MODEL: Found Discogs CatNo "{}"'.format(catno_str))
        return catno_str

    def d_get_all_catnos(self, d_labels):
        '''get all found catalog number from discogs label object concatinated
           with newline'''
        catno_str = ''
        if len(d_labels) == 0:
            log.warning("MODEL: Discogs release without Label/CatNo. "
                        "This is weird!")
        else:
            for cnt, label in enumerate(d_labels):
                if cnt == 0:
                    catno_str = label.data['catno']
                else:
                    catno_str += '\n{}'.format(label.data['catno'])
            log.info('MODEL: Found Discogs CatNo(s) "{}"'.format(catno_str))
        return catno_str

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

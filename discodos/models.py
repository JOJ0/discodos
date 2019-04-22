from discodos.utils import * # most of this should only be in view
from abc import ABC, abstractmethod
from discodos import log, db
from tabulate import tabulate as tab # should only be in view
import pprint
import discogs_client
import discogs_client.exceptions as errors
import requests.exceptions as reqerrors
import urllib3.exceptions as urlerrors
from sqlite3 import Error as sqlerr
import sqlite3
import time

class Database (object):

    def __init__(self, db_conn=False, db_file=False):
        if db_conn:
            log.debug("Database: db_conn argument was handed over.")
            self.db_conn = db_conn
        else:
            log.debug("Database: Creating connection to db_file.")
            if not db_file:
                log.debug("Database: No db_file given, using default name.")
                db_file = './discobase.db'
            self.db_conn = self.create_conn(db_file)

    def create_conn(self, db_file):
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except sqlerr as e:
            log.error("Database: Connection error: %s", e)
        return None

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
                self.info = db.get_mix_info(self.db_conn, self.id)
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
                    mix_id_tuple = db.get_mix_id(db_conn, self.name)
                    log.info('%s', mix_id_tuple)
                    self.id = mix_id_tuple[0]
                    self.id_existing = True
                    self.name_existing = True
                    # load basic mix-info from DB
                    # FIXME info should also be available as single attrs: created, venue, etc.
                    # FIXME or okay? here we assume mix is existing and id could be fetched
                    try:
                        self.info = db.get_mix_info(self.db_conn, self.id)
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


    def delete(self):
        db_return = db.delete_mix(self.db_conn, self.id)
        self.db_conn.commit()
        log.info("MODEL: Deleted mix, DB returned: {}".format(db_return))

    def create(self, _played, _venue, new_mix_name = False):
        if not new_mix_name:
            new_mix_name = self.name
        created_id = db.add_new_mix(self.db_conn, new_mix_name, _played, _venue)
        self.db_conn.commit()
        log.info("MODEL: New mix created with ID {}.".format(created_id))
        return created_id

    def get_all_mixes(self):
        """
        get metadata of all mixes from db

        @param
        @return sqlite fetchall rows object
        @author
        """
        mixes_data = db.get_all_mixes(self.db_conn)
        log.info("MODEL: Returning mixes table")
        return mixes_data

    def get_one_mix_track(self, track_id):
        log.info("MODEL: Returning track {} from {}.".format(track_id, self.id))
        return db.get_one_mix_track(self.db_conn, self.id, track_id)

    def update_track_in_mix(self, track_details, edit_answers):
        try:
            db.update_track_in_mix(self.db_conn,
                track_details['mix_track_id'],
                edit_answers['d_release_id'],
                edit_answers['d_track_no'],
                edit_answers['track_pos'],
                edit_answers['trans_rating'],
                edit_answers['trans_notes'])
            db.update_or_insert_track_ext(self.db_conn,
                track_details['d_release_id'],
                edit_answers['d_release_id'],
                edit_answers['d_track_no'],
                edit_answers['key'],
                edit_answers['key_notes'],
                edit_answers['bpm'],
                edit_answers['notes'],
                )
            log.info("MODEL: Track edit was successful.")
            return True
        except Exception as edit_err:
            log.error("MODEL: Something went wrong in update_track_in_mix!")
            raise edit_err
            return False

    def get_tracks_from_position(self, pos):
        return db.get_tracks_from_position(self.db_conn, self.id, pos)

    def reorder_tracks(self, pos):
        log.info("MODEL: reorder_tracks got pos {}".format(pos))
        tracks_to_shift = db.get_tracks_from_position(self.db_conn, self.id, pos)
        if not tracks_to_shift:
            return False
        for t in tracks_to_shift:
            log.info("MODEL: Shifting mix_track_id %i from pos %i to %i", t['mix_track_id'],
                     t['track_pos'], pos)
            if not db.update_pos_in_mix(self.db_conn, t['mix_track_id'], pos):
                return False
            pos = pos + 1
        return True

    def reorder_tracks_squeeze_in(self, pos, tracks_to_shift):
        log.info("MODEL: reorder_tracks got pos {}".format(pos))
        #tracks_to_shift = db.get_tracks_from_position(self.db_conn, self.id, pos)
        if not tracks_to_shift:
            return False
        for t in tracks_to_shift:
            new_pos = t['track_pos'] + 1
            log.info("MODEL: Shifting mix_track_id %i from pos %i to %i", t['mix_track_id'],
                     t['track_pos'], new_pos)
            if not db.update_pos_in_mix(self.db_conn, t['mix_track_id'], new_pos):
                return False
        return True

    def delete_track(self, pos):
        log.info("MODEL: Deleting track {} from {}.".format(pos, self.id))
        return db.delete_track_from_mix(self.db_conn, self.id, pos)

    def get_full_mix(self, verbosity = "coarse"):
        return db.get_full_mix(self.db_conn, self.id, verbosity)

    def add_track(self, release, track_no, track_pos, trans_rating='', trans_notes=''):
        return db.add_track_to_mix(self.db_conn, self.id, release, track_no, track_pos,
                trans_rating='', trans_notes='')

    def get_last_track(self):
        return db.get_last_track_in_mix(self.db_conn, self.id)

    def get_all_releases(self):
        return db.get_all_releases(self.db_conn, self.id)

    def get_tracks_of_one_mix(self):
        return db.get_tracks_of_one_mix(self.db_conn, self.id)

    def get_all_tracks_in_mixes(self):
        return db.get_all_tracks_in_mixes(self.db_conn)

    def get_tracks_to_copy(self):
        return db.get_mix_tracks_to_copy(self.db_conn, self.id)


# record collection class
class Collection (Database):

    def __init__(self, db_conn, db_file = False):
        self.db_conn = db_conn
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
        return db.all_releases(self.db_conn)

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
        except urlerrors.NewConnectionError as ConnErr:
            log.error("%s", ConnErr)
        except urlerrors.MaxRetryError as RetryErr:
            log.error("%s", RetryErr)
        except Exception as Exc:
            log.error("Exception: %s", Exc)


    def search_release_offline(self, id_or_title):
        if is_number(id_or_title):
            try:
                release = db.search_release_id(self.db_conn, id_or_title)
                if release:
                    #return '| '+str(release[0][0])+' | '+ str(release[0][1])+' | '
                    return [release]
                else:
                    release_not_found = None
                    return release_not_found
            except Exception as Exc:
                log.error("Not found or Database Exception: %s\n", Exc)
                raise Exc
        else:
            try:
                releases = db.search_release_title(self.db_conn, id_or_title)
                if releases:
                    log.debug("First found release: {}".format(releases[0]))
                    log.debug("All found releases: {}".format(releases))
                    # return all releases (so it's a list for tabulate),
                    # but only first one is used later on...
                    #return [releases]
                    return releases
                else:
                    return None
            except Exception as Exc:
                log.error("Not found or Database Exception: %s\n", Exc)
                raise Exc

    def get_all_releases(self):
        return db.all_releases(self.db_conn)

    def create_track(self, release_id, track_no, track_title):
        try:
           return db.create_track(self.db_conn, release_id, track_no, track_title)
        except sqlerr as err:
            log.info("Not added, probably already there.\n")
            log.info("DB returned: %s", err)
            return False

    def search_release_id(self, release_id):
        return db.search_release_id(self.db_conn, release_id)

    def create_release(self, release_id, release_title):
        return db.create_release(self.db_conn, release_id, release_title)

    def get_d_release(self, release_id):
        return self.d.release(release_id)

    def is_in_d_coll(self, release_id):
        successful = False
        for r in self.me.collection_folders[0].releases:
            #self.rate_limit_slow_downer(d, remaining=5, sleep=2)
            if r.release.id == release_id:
                #last_row_id = db.create_release(_conn, r)
                #last_row_id = db.create_release(_conn, r.release.id, r.release.title)
                successful = self.create_release(r.release.id, r.release.title)
                #break
                return r
        if not successful:
            return False

    def rate_limit_slow_downer(self, remaining=10, sleep=2):
        '''Discogs util: stay in 60/min rate limit'''
        if int(self.d._fetcher.rate_limit_remaining) < remaining:
            log.info("Discogs request rate limit is about to exceed,\
                      let's wait a bit: %s\n",
                         self.d._fetcher.rate_limit_remaining)
            time.sleep(sleep)

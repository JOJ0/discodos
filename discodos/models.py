from discodos.utils import * # most of this should only be in view
from abc import ABC, abstractmethod
from discodos import log, db
from tabulate import tabulate as tab # should only be in view
import pprint
import discogs_client
import discogs_client.exceptions as errors
import requests.exceptions as reqerrors
import urllib3.exceptions as urlerrors

# mix model class
class Mix (object):

    def __init__(self, db_conn, mix_name_or_id):
        self.db_conn = db_conn
        # figuring out names and IDs, just logs and sets instance attributes, no exits here! 
        self.name_or_id = mix_name_or_id
        self.id_existing = False
        self.name_existing = False
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

    def delete(self):
        db_return = db.delete_mix(self.db_conn, self.id)
        self.db_conn.commit()
        log.info("MODEL: Deleted mix, DB returned: {}".format(db_return))

    def create(self, _played, _venue):
        created_id = db.add_new_mix(self.db_conn, self.name, _played, _venue)
        self.db_conn.commit()
        log.info("MODEL: New mix created with ID {}.".format(created_id))
        return created_id

    def get_all_mixes(self):
        """
        get metadata of all mixes from db


        @param
        @return
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

    def reorder_tracks(self, pos):
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



# record collection class
class Collection (object):

    def __init__(self, db_conn):
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




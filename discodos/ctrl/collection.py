import logging
from abc import ABC
# import pprint as p
from time import time
import discogs_client.exceptions as errors
from rich.progress import (BarColumn, MofNCompleteColumn, Progress,
                           TaskProgressColumn, )

from discodos.ctrl.common import ControlCommon
from discodos.model_brainz import Brainz
from discodos.model_brainz_match import Brainz_match
from discodos.model_collection import Collection
from discodos.utils import is_number
from discodos.view import CollectionViewCommandline, DiscodosListApp

log = logging.getLogger('discodos')


class CollectionControlCommon (ABC):
    """Common controller functionality for the Discogs user profile"""
    def __init__(self):
        pass


class CollectionControlCommandline (ControlCommon, CollectionControlCommon):
    """CLI level controller functionality, offline & Discogs user profile"""

    def __init__(
        self,
        db_conn,
        user_int,
        userToken,
        appIdentifier,
        db_file=False,
        musicbrainz_user=False,
        musicbrainz_pass=False,
    ):
        self.user = user_int  # set instance of User_int class as attribute
        self.cli = (
            CollectionViewCommandline()
        )  # instantiate cli frontend class
        self.collection = Collection(db_conn, db_file)

        if self.collection.db_not_found is True:
            self.cli.ask("Setting up DiscoBASE, press enter...")
            super().setup_db(db_file)
            self.collection = Collection(db_conn, db_file)

        if self.user.WANTS_ONLINE:
            if not self.collection.discogs_connect(userToken, appIdentifier):
                log.error("connecting to Discogs API, let's stay offline!\n")
            else:  # only try to initialize brainz if discogs is online already
                self.brainz = Brainz(
                    musicbrainz_user, musicbrainz_pass, appIdentifier
                )
        print()
        log.info("CTRL: ONLINE=%s in %s", self.ONLINE, __class__.__name__)
        self.first_track_on_release = ""

    @property
    def ONLINE(self):
        status = self.collection.ONLINE
        log.debug(
            "CTRL: ONLINE=%s in %s", status, self.collection.__class__.__name__
        )
        return status

    @property
    def d(self):
        discogs_client = self.collection.d
        log.debug(
            "CTRL: Retrieving %s instance from %s",
            discogs_client.__class__.__name__,
            self.collection.__class__.__name__
        )
        return discogs_client

    @property
    def me(self):
        discogs_me = self.collection.me
        log.debug(
            "CTRL: Retrieving %s instance from %s",
            discogs_me.__class__.__name__,
            self.collection.__class__.__name__,

        )
        return discogs_me

    def search_release(self, _searchterm):  # online or offline search is
        if self.collection.ONLINE:          # decided in this method
            if is_number(_searchterm):
                self.cli.p('Searchterm is a number, trying to add Release ID '
                           'to collection...')
                if not self.add_release(int(_searchterm)):
                    log.warning("Release wasn't added to Collection, "
                                "continuing anyway.")
            db_releases = self.collection.get_all_db_releases()
            self.cli.p('Searching Discogs for Release ID or Title: {}'.format(
                _searchterm))
            search_results = self.collection.search_release_online(_searchterm)
            # SEARCH RESULTS OUTPUT HAPPENS HERE
            compiled_results_list = self.print_and_return_first_d_release(
                search_results,
                _searchterm,
                db_releases
            )
            if compiled_results_list is None:
                self.cli.error_not_the_release()
                m = 'Try altering your search terms!'
                log.info(m)
                print(m)
                raise SystemExit(1)
            return compiled_results_list

        else:
            self.cli.p('Searching database for ID or Title: {}'.format(_searchterm))
            search_results = self.collection.search_release_offline(_searchterm)
            if not search_results:
                self.cli.p('Nothing found.')
                return
            else:
                self.cli.p('Found releases:')
                if isinstance(search_results, list):
                    for cnt, release in enumerate(search_results):
                        self.cli.p('({}) {} - {}'.format(cnt, release[3], release[1]))
                    answ = self.cli.ask('Which release? (0) ')
                    answ = 0 if answ == '' else int(answ)
                else:
                    self.cli.p('{} - {}'.format(search_results[3], search_results[1]))
                    return [search_results]
                return [search_results[answ]]

    def print_and_return_first_d_release(self, discogs_results, _searchterm,
                                         _db_releases):
        ''' formatted output _and return of Discogs release search results'''
        self.first_track_on_release = ''  # reset this in any case first
        # only show pages count if it's a Release Title Search
        if not is_number(_searchterm):
            if discogs_results:
                self.cli.p("Found {} page(s) of results.".format(
                    discogs_results.pages))
            else:
                return None
        else:
            self.cli.p("ID: {}, Title: {}".format(
                discogs_results[0].id,
                discogs_results[0].title))
        for result_item in discogs_results:
            self.cli.p("Checking " + str(result_item.id))
            for dbr in _db_releases:
                if result_item.id == dbr['discogs_id']:
                    self.cli.p("Good, first matching record in your collection is:")
                    release_details = self.collection.prepare_release_info(result_item)
                    tracklist = self.collection.prepare_tracklist_info(
                        result_item.id, result_item.tracklist)
                    print('{}\n'.format(self.cli.join_links_to_str(dbr)))
                    # we need to pass a list in list here. we use tabulate to view
                    self.cli.tab_online_search_results([release_details])
                    self.cli.online_search_results_tracklist(tracklist)
                    self.first_track_on_release = result_item.tracklist[0].position
                    break
            try:
                if result_item.id == dbr['discogs_id']:
                    log.info("Compiled Discogs release_details: {}".format(release_details))
                    return release_details
            except UnboundLocalError:
                log.error("Discogs collection was not imported to DiscoBASE. Use 'disco import' command!")
                # raise unb
                raise SystemExit(1)
        return None

    def view_all_releases(self):
        self.cli.p("Showing all releases in DiscoBASE.")
        all_releases_result = self.collection.get_all_db_releases()
        self.cli.tab_all_releases(all_releases_result)

    def track_report(self, track_searchterm):
        release = self.search_release(track_searchterm)
        if release:
            if self.collection.ONLINE == True:
                track_no = self.cli.ask_for_track(
                    suggest=self.first_track_on_release)
                rel_id = release['id']
                rel_name = release['title']
            else:
                track_no = self.cli.ask_for_track()
                rel_id = release[0]['discogs_id']
                rel_name = release[0]['discogs_title']
            track_occurences = self.collection.track_report_occurences(rel_id, track_no)
            tr_sugg_msg = '\nTrack combo suggestions for {} on "{}".'.format(
                track_no, rel_name)
            tr_sugg_msg+= '\nThis is how you used this track in the past:'
            self.cli.p(tr_sugg_msg)
            if track_occurences:
                for tr in track_occurences:
                    self.cli.p('Snippet of Mix {} - "{}":'.format(
                        tr['mix_id'], tr['name']))
                    report_snippet = self.collection.track_report_snippet(tr['track_pos'], tr['mix_id'])
                    self.cli.tab_mix_table(report_snippet, _verbose = True)
        else:
            raise SystemExit(3)

    # ADD RELEASE TO COLLECTION
    def add_release(self, release_id):
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)
        if not is_number(release_id):
            log.error('Not a number')
            return False
        else:
            # setup.py argparser catches non-int, this is for calls from elsewhere
            if self.collection.search_release_id(release_id):
                msg = "Release ID is already existing in DiscoBASE, "
                msg+= "won't add it to your Discogs collection. We don't want dups!"
                self.cli.p(msg)
            else:
                self.cli.p("Asking Discogs if release ID {:d} is valid.".format(
                           release_id))
                result = self.collection.get_d_release(release_id)
                if result:
                    artists = self.collection.d_artists_to_str(result.artists)
                    d_catno = self.collection.d_get_first_catno(result.labels)
                    log.debug(dir(result))
                    self.cli.p("Adding \"{}\" to collection".format(result.title))
                    for folder in self.collection.me.collection_folders:
                        if folder.id == 1:
                            folder.add_release(release_id)
                            last_row_id = self.collection.create_release(
                                result.id, result.title, artists, d_catno,
                                d_coll=True
                            )
                    if not last_row_id:
                        self.cli.error_not_the_release()
                    log.debug("Discogs release was maybe added to Collection")
                    self.cli.duration_stats(start_time, 'Adding Release to Collection')
                    return True
                else:
                    log.debug("No Discogs release. Returning False")
                    self.cli.duration_stats(start_time, 'Adding Release to Collection')
                    return False

    # import specific release ID into DB
    def import_release(self, _release_id):
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)
        # print(dir(me.collection_folders[0].releases))
        # print(dir(me))
        # print(me.collection_item)
        # if not force == True:
        self.cli.p("Asking Discogs for release ID {:d}".format(
                   _release_id))
        result = self.collection.get_d_release(_release_id)
        if not result:
            raise SystemExit(3)
        else:
            self.cli.p("Release ID is valid: {}\n".format(result.title) +
                       "Let's see if it's in your collection, "
                       "this might take some time...")
            in_coll = self.collection.is_in_d_coll(_release_id)
            if in_coll:
                artists = self.collection.d_artists_to_str(in_coll.release.artists)
                d_catno = self.collection.d_get_first_catno(in_coll.release.labels)
                self.cli.p(
                    "Found it in collection: {} - {} - {}.\n"
                    "Importing to DiscoBASE.".format(
                        in_coll.release.id, artists, in_coll.release.title))
                self.collection.create_release(
                    in_coll.release.id, in_coll.release.title,
                    artists, d_catno, d_coll=True)
            else:
                self.cli.error_not_the_release()
        self.cli.duration_stats(start_time, 'Discogs import')

    def import_collection(self, tracks=False):
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)
        self.releases_processed = 0
        self.releases_added = 0
        self.releases_db_errors = 0
        if tracks:
            self.cli.p("Importing Discogs collection into DiscoBASE (extended import - releases and tracks)")
            self.tracks_processed = 0
            self.tracks_added = 0
            self.tracks_db_errors = 0
            self.tracks_discogs_errors = 0
        else:
            self.cli.p("Importing Discogs collection into DiscoBASE (regular import - just releases)")

        for item in self.collection.me.collection_folders[0].releases:
            self.collection.rate_limit_slow_downer(remaining=15, sleep=3)
            d_artists = item.release.artists  # we'll need it again with tracks
            artists = self.collection.d_artists_to_str(d_artists)
            first_catno = self.collection.d_get_first_catno(item.release.labels)
            print('Release {} - "{}" - "{}"'.format(item.release.id, artists,
                  item.release.title))
            rel_created = self.collection.create_release(
                item.release.id, item.release.title, artists, first_catno,
                d_coll=True
            )
            # create_release will return False if unsuccessful
            if rel_created:
                self.releases_added += 1
            else:
                self.releases_db_errors += 1
                log.error(
                    'importing release "{}" '
                    'Continuing anyway.'.format(item.release.title))
            if tracks:
                try:
                    tracklist = item.release.tracklist
                    for track in tracklist:
                        tr_artists = self.collection.d_artists_parse(
                            tracklist, track.position, d_artists)
                        tr_title = track.title
                        if self.collection.upsert_track(
                            item.release.id, track.position, tr_title,
                            tr_artists
                        ):
                            self.tracks_added += 1
                            msg_tr_add = 'Track "{}" - "{}"'.format(
                                tr_artists, tr_title)
                            log.info(msg_tr_add)
                            print(msg_tr_add)
                        else:
                            self.tracks_db_errors += 1
                            log.error('importing track. Continuing anyway.')
                except Exception as Exc:
                    self.tracks_discogs_errors += 1
                    log.error("Exception: %s", Exc)

            msg_rel_add="Releases so far: {}".format(self.releases_added)
            log.info(msg_rel_add)
            print(msg_rel_add)
            if tracks:
                msg_trk_add="Tracks so far: {}".format(self.tracks_added)
                log.info(msg_trk_add)
                print(msg_trk_add)
            print()  # leave some space after a release and all its tracks
            self.releases_processed += 1

        print('Processed releases: {}. Imported releases to DiscoBASE: {}.'.format(
            self.releases_processed, self.releases_added))
        print('Database errors (release import): {}.'.format(
            self.releases_db_errors))

        if tracks:
            print('Processed tracks: {}. Imported tracks to DiscoBASE: {}.'.format(
                self.tracks_processed, self.tracks_added))
            print('Database errors (track import): {}. Discogs errors (track import): {}.'.format(
                self.tracks_db_errors, self.tracks_discogs_errors))

        self.cli.duration_stats(start_time, 'Discogs import')  # print time stats

    def bpm_report(self, bpm, pitch_range):
        possible_tracks = self.collection.get_tracks_by_bpm(bpm, pitch_range)
        tr_sugg_msg = '\nShowing tracks with a BPM around {}. Pitch range is +/- {}%.'.format(bpm, pitch_range)
        self.cli.p(tr_sugg_msg)
        if possible_tracks:
            max_width = self.cli.get_max_width(
                possible_tracks, ['chosen_key', 'chosen_bpm'], 3
            )
            for tr in possible_tracks:
                key_bpm_and_space = self.cli.combine_fields_to_width(
                    tr, ['chosen_key', 'chosen_bpm'], max_width
                )
                catno = tr['d_catno'].replace(' ', '')
                self.cli.p(
                    '{}{} - {} [{} ({}) {}]'.format(
                        key_bpm_and_space,
                        tr['d_artist'],
                        tr['d_track_name'],
                        catno,
                        tr['d_track_no'],
                        tr['discogs_title']
                    )
                )

    def key_report(self, key):
        possible_tracks = self.collection.get_tracks_by_key(key)
        tr_sugg_msg = '\nShowing tracks with key {}'.format(key)
        self.cli.p(tr_sugg_msg)
        if possible_tracks:
            max_width = self.cli.get_max_width(
                possible_tracks, ['chosen_key', 'chosen_bpm'], 3
            )
            for tr in possible_tracks:
                # print("in key_report: {}".format(tr['chosen_key']))
                # print("in key report: {}".format(tr['chosen_bpm']))
                key_bpm_and_space = self.cli.combine_fields_to_width(
                    tr, ['chosen_key', 'chosen_bpm'], max_width
                )
                self.cli.p(
                    '{}{} - {} [{} ({}) {}]:'.format(
                        key_bpm_and_space,
                        tr['d_artist'],
                        tr['d_track_name'],
                        tr['d_catno'],
                        tr['d_track_no'],
                        tr['discogs_title']
                    )
                )

    def key_and_bpm_report(self, key, bpm, pitch_range):
        possible_tracks = self.collection.get_tracks_by_key_and_bpm(key, bpm, pitch_range)
        tr_sugg_msg = '\nShowing tracks with key "{}" and a BPM around {}. Pitch range is +/- {}%.'.format(key, bpm, pitch_range)
        self.cli.p(tr_sugg_msg)
        if possible_tracks:
            max_width = self.cli.get_max_width(
                possible_tracks, ['chosen_key', 'chosen_bpm'], 3
            )
            for tr in possible_tracks:
                key_bpm_and_space = self.cli.combine_fields_to_width(
                    tr, ['chosen_key', 'chosen_bpm'], max_width
                )
                self.cli.p(
                    '{}{} - {} [{} ({}) {}]:'.format(
                        key_bpm_and_space,
                        tr['d_artist'],
                        tr['d_track_name'],
                        tr['d_catno'],
                        tr['d_track_no'],
                        tr['discogs_title']
                    )
                )

    def update_tracks_from_discogs(self, track_list, offset=0):
        '''takes a list of tracks and updates tracknames/artists from Discogs.
           List has to contain fields: d_release_id, discogs_title, d_track_no.
           Usually list items are slite Row objects, but could be dicts too.
           Any iterable should work unless it doesn't have named keys!
        '''
        start_time = time()
        if offset:
            self.processed = offset
            self.processed_total = len(track_list) + offset
        else:
            self.processed = 1
            self.processed_total = len(track_list)
        self.tracks_added = 0
        self.tracks_db_errors = 0
        self.tracks_not_found_errors = 0
        for track in track_list:

            d_track_no = track['d_track_no']
            d_release_id = track['d_release_id']
            discogs_title = track['discogs_title']
            self.collection.rate_limit_slow_downer(remaining=20, sleep=3)

            # move this to method fetch_track_and_artist_from_discogs
            try: # we catch 404 here, and not via get_d_release, to save one request
                name, artist = "", ""
                d_tracklist = self.d.release(d_release_id).tracklist
                name = self.collection.d_tracklist_parse(
                    d_tracklist, d_track_no)
                artist = self.collection.d_artists_parse(
                    d_tracklist, d_track_no,
                    self.d.release(d_release_id).artists)
            except errors.HTTPError as HtErr:
                log.error('Track {} on "{}" ({}) not existing on Discogs ({})'.format(
                    d_track_no, discogs_title, d_release_id, HtErr))
                self.cli.brainz_processed_so_far(self.processed, self.processed_total)
                self.processed += 1
                print("")  # space for readability
                continue  # jump to next iteration, nothing more to do here

            if name or artist:
                print('Adding Track {} on "{}" ({})'.format(
                      d_track_no, discogs_title, d_release_id))
                print('{} - {}'.format(artist, name))
                if self.collection.upsert_track(
                    d_release_id, d_track_no, name, artist
                ):
                    self.tracks_added += 1
                else:
                    self.tracks_db_errors += 1
                self.cli.brainz_processed_so_far(self.processed, self.processed_total)
                self.processed += 1
                print("")  # space for readability
            else:
                print('Either track or artist name not found on '
                      '"{}" ({}) - Track {} really existing?'.format(
                          discogs_title, d_release_id, d_track_no))
                self.tracks_not_found_errors += 1
                self.cli.brainz_processed_so_far(self.processed, self.processed_total)
                self.processed += 1
                print("")  # space for readability

        if offset:
            processed_real = self.processed_total - offset
        else:
            processed_real = self.processed_total
        print('Processed: {}. Added Artist/Track info to DiscoBASE: {}.'.format(
            processed_real, self.tracks_added))
        print('Database errors: {}. Not found on Discogs errors: {}.'.format(
            self.tracks_db_errors, self.tracks_not_found_errors))
        print("")  # space for readability

        self.cli.duration_stats(start_time, 'Updating track info') # print time stats
        return True # we did at least something and thus were successfull

    def update_single_track_or_release_from_discogs(self, rel_id, rel_title,
                                                    track_no):
        if not track_no:
            track_no = self.cli.ask_for_track(suggest = self.first_track_on_release)
        if track_no == '*' or track_no == 'all':
            full_release = self.collection.get_d_release(rel_id)
            tr_list = []
            for tr in full_release.tracklist:
                tr_list.append({
                    'd_release_id': rel_id,
                    'discogs_title': rel_title,
                    'd_track_no': tr.position
                })
        else:
            tr_list = [{
                'd_release_id': rel_id,
                'discogs_title': rel_title,
                'd_track_no': track_no
            }]
        return self.update_tracks_from_discogs(tr_list)

    def update_tracks_from_brainz(self, track_list, detail=1, offset=0):
        # catch errors. this is a last resort check. prettier err-msgs earlier!
        if track_list == [None] or track_list == [] or track_list == None:
            log.error("Didn't get sufficient data for *Brainz update. Quitting.")
            return False
        start_time = time()
        log.debug('CTRL: update_track_from_brainz: '
                  'match detail option is: {}'.format(detail))
        if offset:
            processed = offset
            processed_total = len(track_list) + offset -1
        else:
            processed = 1
            processed_total = len(track_list)
        errors_not_found, errors_db, errors_no_release = 0, 0, 0
        errors_no_rec_MB, errors_no_rec_AB, errors_not_imported = 0, 0, 0
        added_release, added_rec, added_key, added_chords_key, added_bpm = 0, 0, 0, 0, 0
        warns_discogs_fetches = 0
        for track in track_list:
            release_mbid, rec_mbid = None, None  # we are filling these
            key, chords_key, bpm = None, None, None  # searched later, in this order
            # d_release_id = track['d_release_id']  # from track table
            discogs_id = track['discogs_id']  # from release table
            d_track_no = track['d_track_no']
            user_rec_mbid = track['m_rec_id_override']

            log.info('CTRL: Trying to match Discogs release {} "{}"...'.format(
                discogs_id, track['discogs_title']))
            d_rel = self.collection.get_d_release(discogs_id) # 404 is handled here

            def _warn_skipped(m):  # prints skipped-message and processed-count
                log.warning(m)
                self.cli.brainz_processed_so_far(processed, processed_total)
                print('')  # space for readability

            if not d_rel:
                m = "Skipping. Cant't fetch Discogs release."
                _warn_skipped(m)
                processed += 1
                continue  # jump to next track
            else:
                if not track['d_track_no']:  # no track number in db -> not imported
                    # FIXME errors_not_imported
                    m = f'Skipping. No track number for '
                    m+= f'"{track["discogs_title"]}" in DiscoBASE.\n'
                    m+= f'Did you import Track details from Discogs yet? (-u)'
                    _warn_skipped(m)
                    errors_not_imported += 1
                    processed += 1
                    continue  # jump to next track
                elif not track['d_track_name']:  # no track name in db -> ask discogs
                    # FIXME why was get_d_release needed here? it's above already???
                    # d_rel = self.collection.get_d_release(discogs_id) # 404 is handled here
                    log.warning('No track name in DiscoBASE, asking Discogs...')
                    d_track_name = self.collection.d_tracklist_parse(
                        d_rel.tracklist, track['d_track_no'])
                    if not d_track_name:  # no track name on Discogs -> give up
                        m = f'Skipping. Track number {track["d_track_no"]} '
                        m+= f'not existing on release "{track["discogs_title"]}"'
                        _warn_skipped(m)
                        errors_not_found += 1
                        processed += 1
                        continue  # jump to next track
                    print(f'Track name found on Discogs: "{d_track_name}"')
                    warns_discogs_fetches += 1
                else:
                    d_track_name = track['d_track_name']  # track name in db, good

                if not track['d_catno']:  # no CatNo in db -> ask discogs
                    log.warning('No catalog number in DiscoBASE, asking Discogs...')
                    d_catno = d_rel.labels[0].data['catno']
                    print(f'Catalog number found on Discogs: "{d_catno}"')
                    warns_discogs_fetches += 1
                else:
                    d_catno = track['d_catno']

                if not track['d_artist']: # no artist name in db -> ask discogs
                    log.warning('No artist name in DiscoBASE, asking Discogs...')
                    d_artist = self.collection.d_artists_parse(d_rel.tracklist,
                          d_track_no, d_rel.artists)
                    print(f'Artist found on Discogs: "{d_artist}"')
                    warns_discogs_fetches += 1
                else:
                    d_artist = track['d_artist']

                # get_discogs track number numerical
                # print(dir(d_rel.tracklist[1]))
                # d_rel_track_count = len(d_rel.tracklist)
                d_track_numerical = self.collection.d_tracklist_parse_numerical(
                    d_rel.tracklist, d_track_no)

            # initialize the brainz match class here,
            # we pass it the prepared track data we'd like to match,
            # detailed modifications are done inside (strip spaces, etc)
            bmatch = Brainz_match(self.brainz.musicbrainz_user,
                                  self.brainz.musicbrainz_password,
                                  self.brainz.musicbrainz_appid,
              discogs_id, track['discogs_title'], d_catno,
              d_artist, d_track_name, d_track_no,
              d_track_numerical)
            # fetching of mb_releases controllable from outside
            # (reruns with different settings)
            bmatch.fetch_mb_releases(detail = detail)
            release_mbid = bmatch.match_release()
            if not release_mbid and not user_rec_mbid:
                log.info('CTRL: No MusicBrainz release matches. Sorry dude!')
            else: # Recording MBID search
                if user_rec_mbid:
                    rec_mbid = user_rec_mbid
                else:
                    bmatch.fetch_mb_matched_rel()
                    rec_mbid = bmatch.match_recording()

                if rec_mbid: # we where lucky...
                    # get accousticbrainz info
                    key = bmatch.get_accbr_key(rec_mbid)
                    if key is not None: # Skip if Rec MBID not on AcBr yet
                        chords_key = bmatch.get_accbr_chords_key(rec_mbid)
                        bpm = bmatch.get_accbr_bpm(rec_mbid)
                    else:
                        chords_key = None
                        bpm = None
                        errors_no_rec_AB += 1
                else:
                    errors_no_rec_MB += 1
            # user reporting starts here, not in model anymore
            # summary and save only when we have Release MBID or user_rec_mbid
            if release_mbid or user_rec_mbid:
                print("Adding Brainz info for track {} on {} ({})".format(
                    track['d_track_no'],  track['discogs_title'],
                    discogs_id))
                print("{} - {}".format(d_artist, d_track_name))
                if release_mbid:
                    print("Release MBID: {}".format(release_mbid))
                else:
                    log.warning("No Release MBID found!!!")

                if not rec_mbid:
                    log.warning("No Recording MBID found!!!")
                else:
                    if user_rec_mbid:
                        print("Recording MBID: {} (user override)".format(rec_mbid))
                    else:
                        print("Recording MBID: {}".format(rec_mbid))

                print("Key: {}  |  Chords Key: {}  |  BPM: {}".format(
                    key if key else '---',
                    chords_key if chords_key else '---',
                    bpm if bpm else '---')
                )

                # update release table
                ok_release = self.collection.update_release_brainz(discogs_id,
                    release_mbid, bmatch.release_match_method)
                if ok_release:
                    log.info('Release table updated successfully.')
                    added_release += 1
                else:
                    log.error('while updating release table. Continuing anyway.')
                    errors_db += 1

                # update track and track_ext table
                ok_rec = self.collection.upsert_track_brainz(discogs_id,
                    track['d_track_no'], rec_mbid, bmatch.rec_match_method,
                    key, chords_key, bpm)

                if ok_rec:
                    if rec_mbid: added_rec += 1
                    log.info('Track table updated successfully.')
                    if key: added_key += 1
                    if chords_key: added_chords_key += 1
                    if bpm: added_bpm += 1
                else:
                    log.error('while updating track table. Continuing anyway.')
                    errors_db += 1

            else:
                errors_no_release += 1
                log.warning('No Release MBID found for track {} on Discogs release "{}"'.format(
                        track['d_track_no'], track['discogs_title']))
            self.cli.brainz_processed_so_far(processed, processed_total)
            processed += 1
            print('')  # space for readability

        if offset:
            processed_real = processed_total - offset
        else:
            processed_real = processed_total
        self.cli.brainz_processed_report(processed_real, added_release,
          added_rec, added_key, added_chords_key, added_bpm, errors_db,
          errors_not_found, errors_no_rec_AB, errors_not_imported,
          warns_discogs_fetches)
        self.cli.duration_stats(start_time, 'Updating track info') # print time stats
        return True  # we are through all tracks, in any way, this is a success

    def update_all_tracks_from_brainz(self, detail=1, offset=0, force=False,
                                      skip_unmatched=False):
        if not self.ONLINE:
            self.cli.p("Not online, can't pull from AcousticBrainz...")
            return False  # exit method we are offline
        tracks = self.collection.get_all_tracks_for_brainz_update(
              offset=offset, really_all=force, skip_unmatched=skip_unmatched)
        match_ret = self.update_tracks_from_brainz(tracks, detail,
              offset=offset)
        return match_ret

    def update_single_track_or_release_from_brainz(self, rel_id, rel_title,
                                                   track_no, detail):
        def _err_cant_fetch(tr_no):
            m = 'Can\'t fetch "{}" on "{}". '.format(tr_no, rel_title)
            m+= 'Either track number not existing on release or '
            m+= 'track not imported into DiscoBASE yet. Try '
            m+= '"disco search ... -u", then re-run match-command.'
            log.error(m)

        if not track_no:
            track_no = self.cli.ask_for_track(suggest = self.first_track_on_release)

        if track_no == '*' or track_no == 'all':
            full_release = self.collection.get_d_release(rel_id)
            tr_list = []
            for tr in full_release.tracklist:
                db_track = self.collection.get_track_for_brainz_update(rel_id, tr.position.upper())
                if db_track == None:
                    _err_cant_fetch(tr.position.upper())
                else: # only fetch track for brainz update if it is in db, matching would fail anyway
                    tr_list.append(db_track)
        else:
            track = self.collection.get_track_for_brainz_update(rel_id, track_no.upper())
            if track == None:
                _err_cant_fetch(track_no.upper())
                return False
            tr_list = [track]

        return self.update_tracks_from_brainz(tr_list, detail)

    def edit_track(self, rel_id, rel_title, track_no):
        if not track_no:
            track_no = self.cli.ask_for_track(suggest = self.first_track_on_release)
        track_details = self.collection.get_track(rel_id, track_no.upper())
        if track_details == None:
            m = 'Can\'t fetch "{}" on "{}". '.format(track_no, rel_title)
            m+= 'Either the track number is not existing on the release or the '
            m+= 'track was not imported to DiscoBASE yet. Try '
            m+= '"disco search ... -u" first, then re-run edit-command.'
            log.error(m)
            return False
        msg_editing ='Editing track {} on "{}".\n'.format(track_no, rel_title)
        msg_editing+='* to keep a value as is, press enter\n'
        msg_editing+='* text in (braces) shows current value'
        self.cli.p(msg_editing)
        self.cli.p("{} - {} - {}".format(
                   rel_title,
                   track_details['d_track_no'],
                   track_details['d_track_name']))
        log.info("current d_release_id: %s", track_details['d_release_id'])
        edit_answers = self.cli.edit_ask_details(track_details,
                self.cli._edit_track_questions)
        for a in edit_answers.items():
            log.info("answers: %s", str(a))
        update_ok = self.collection.upsert_track_ext(track_details, edit_answers)
        if update_ok:
            self.cli.p("Track edit was successful.")
        else:
            log.error("Something went wrong on track edit!")
            raise SystemExit(1)

    def view_stats(self):
        self.cli.tab_stats(
            self.collection.stats_releases_total(),
            self.collection.stats_releases_matched(),
            self.collection.stats_tracks_total(),
            self.collection.stats_tracks_matched(),
            self.collection.stats_releases_d_collection_flag(),
            self.collection.stats_releases_d_collection_online(),
            self.collection.stats_mixtracks_total(),
            self.collection.stats_mixtracks_unique(),
            self.collection.stats_tracks_key_brainz(),
            self.collection.stats_tracks_key_manual(),
            self.collection.stats_tracks_bpm_brainz(),
            self.collection.stats_tracks_bpm_manual(),
        )

    def ls_releases(self, search_terms):
        """search_terms is a key value dict: eg: d_artist: artistname"""

        search_results = []
        self.cli.p('Searching database for: {}'.format(search_terms))
        try:
            search_results = self.collection.key_value_search_releases(
                search_key_value=search_terms
            )
        except Exception as error:
            self.cli.p(error)

        if not search_results:
            self.cli.p('Nothing found.')
        else:
            self.cli.p('Found releases:')
            self.cli.tab_ls_releases(search_results)

    def import_sales_inventory(self):
        """Import sales inventory"""
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)
        self.cli.p("Importing Discogs sales inventory into DiscoBASE...")
        custom_progress = Progress(
            MofNCompleteColumn(),
            BarColumn(),
            TaskProgressColumn(),
        )
        total_items = len(self.collection.me.inventory)

        with custom_progress:
            task = custom_progress.add_task(
                "[cyan] Status: ",
                total=total_items,
            )
            for item in self.collection.me.inventory:
                self.collection.create_sales_entry(item.release.id, item.id)
                custom_progress.update(task, advance=1)

        self.cli.duration_stats(start_time, 'Inventory import')

    def tui_ls_releases(self, search_terms):
        """search_terms is a key value dict: eg: d_artist: artistname"""

        search_results = []
        self.cli.p('Searching database for: {}'.format(search_terms))
        try:
            search_results = self.collection.key_value_search_releases(
                search_key_value=search_terms
            )
        except Exception as error:
            self.cli.p(error)

        if not search_results:
            self.cli.p('Nothing found.')
            return

        app = DiscodosListApp(
            rows=search_results,
            headers=[
                "ID",
                "Cat. #",
                "Artist",
                "Title",
                "D. Coll.",
                "For Sale",
            ],
            discogs_me=self.me
        )
        app.run(inline=True)
        return

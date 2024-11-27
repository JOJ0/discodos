import logging
from abc import ABC
# import pprint as p
from time import time
from datetime import datetime
from json import JSONDecodeError
import discogs_client.exceptions as errors
from discogs_client import CollectionItemInstance, Sort
from rich.progress import (BarColumn, MofNCompleteColumn, Progress,
                           TaskProgressColumn, SpinnerColumn, TimeElapsedColumn)
from rich import print
from rich.prompt import Prompt, FloatPrompt, Confirm
from rich.panel import Panel

from discodos.ctrl.common import ControlCommon
from discodos.model import Brainz
from discodos.model import Brainz_match
from discodos.model import Collection
from discodos.utils import is_number
from discodos.view import CollectionViewCommandline
from discodos.ctrl.tui import DiscodosListApp
from discodos.utils import extract_discogs_id_regex, RECORD_CHOICES, SLEEVE_CHOICES

log = logging.getLogger('discodos')
custom_progress = Progress(
    MofNCompleteColumn(),
    BarColumn(),
    TaskProgressColumn(),
    TimeElapsedColumn(),
)

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

            # Determine search term or ID
            search_for = _searchterm
            extracted_id = extract_discogs_id_regex(_searchterm)
            if extracted_id:
                print(
                    "Searchterm is a number or Discogs URL, trying to add it "
                    "to the collection..."
                )
                if not self.add_release(extracted_id):
                    log.warning(
                        "Release wasn't added to Collection, continuing anyway."
                    )
                search_for = extracted_id

            db_releases = self.collection.get_all_db_releases()
            print(f"\n[bold]Searching Discogs for:[/bold] {search_for}")
            search_results = self.collection.search_release_online(search_for)

            # Search results output
            compiled_results_list = self.print_and_return_first_d_release(
                search_results,
                search_for,
                db_releases
            )
            if not compiled_results_list:
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

    # Import & remove single release to collection

    def add_release(self, release_id):
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)
        if not is_number(release_id):
            log.error('Not a number')
            return False
        else:
            # setup.py argparser catches non-int, this is for calls from elsewhere
            if self.collection.get_release_by_id(release_id):
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

    def import_release(self, release_id):
        """Import a specific collection release into the DiscoBASE."""
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)

        with custom_progress as progress:
            task1 = progress.add_task("...",start=1, total=5)

            progress.console.print(f"Looking up {release_id:d} on Discogs")
            result = self.collection.get_d_release(release_id)
            progress.update(task1, advance=1)
            if not result:
                raise SystemExit(3)

            progress.console.print(f"Release ID is valid: {result.title}")
            progress.update(task1, advance=1)
            progress.console.print("Let's find it in your Discogs collection")
            coll_item = self.collection.release_from_collection(release_id)
            progress.update(task1, advance=1)

            if coll_item:
                artists = self.collection.d_artists_to_str(coll_item.artists)
                d_catno = self.collection.d_get_first_catno(coll_item.labels)
                progress.console.print(
                    "Found and importing: "
                    f"{coll_item.id} - {artists} - {coll_item.title}"
                )
                self.collection.create_release(
                    coll_item.id,
                    coll_item.title,
                    artists,
                    d_catno,
                    d_coll=True,
                )
            else:
                self.cli.error_not_the_release()

            progress.update(task1, advance=1)
            self.cli.duration_stats(start_time, "Discogs import")
            progress.update(task1, completed=5)

    def remove_and_delete_release(self, release_id):
        """Remove all from collection and delete from DB."""
        coll_items = self.collection.fetch_collection_item_instances(release_id)

        for instance in coll_items:
            print(self.cli.two_column_view(instance))
            delete = Confirm.ask("Remove from Discogs collection?", default=False)
            if not delete:
                continue
            folder = self.collection.me.collection_folders[0]
            folder.remove_release(instance['full_instance'])

        delete_db = Confirm.ask("Remove from DiscoBASE?", default=False)
        if delete_db:
            tracks = self.collection.get_release_tracks_by_id(release_id)
            for track in tracks:
                print(
                    Panel.fit(
                        self.cli.two_column_view(track, as_is=True, skip_empty=True),
                        title=f"Track {track['d_track_no']}",
                    )
                )
            sure = Confirm.ask("Sure?", default=False)
            if sure:
                self.collection.delete_release(release_id)
                return
        log.warning("Kept release in DiscoBASE!")
        return

    # Import collection and helpers

    def process_tracks(self, release_id, tracklist, d_artists):
        tracks_added = 0
        tracks_db_errors = 0
        tracks_discogs_errors = 0

        try:
            for track in tracklist:
                tr_artists = self.collection.d_artists_parse(
                    tracklist, track.position, d_artists
                )
                tr_title = track.title
                if self.collection.upsert_track(
                    release_id, track.position, tr_title, tr_artists
                ):
                    tracks_added += 1
                    # msg_tr_add = f'Track "{tr_artists}" - "{tr_title}"'
                    # log.info(msg_tr_add)
                    # print(msg_tr_add)
                else:
                    tracks_db_errors += 1
                    log.error("importing track. Continuing anyway.")
        except Exception as Exc:
            tracks_discogs_errors += 1
            log.error("Exception: %s", Exc)

        return tracks_added, tracks_db_errors, tracks_discogs_errors

    def create_release_entry(self, item):
        d_artists = item.release.artists
        artists = self.collection.d_artists_to_str(d_artists)
        first_catno = self.collection.d_get_first_catno(item.release.labels)
        self.print_release_info(item.release.id, artists, item.release.title)

        rel_created = self.collection.create_release(
            item.release.id, item.release.title, artists, first_catno,
            d_coll=True
        )
        return rel_created, d_artists, artists

    def print_release_info(self, release_id, artists, title):
        print(f'Release {release_id} - "{artists}" - "{title}"')

    def import_collection(self, tracks=False, offset=0):
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)

        releases_processed = releases_added = releases_db_errors = 0
        tracks_processed = tracks_added = tracks_db_errors = tracks_discogs_errors = 0
        real_releases_processed = 0  # In case we start at offset, we need two counts

        if tracks:
            self.cli.p(
                "Importing Discogs collection into DiscoBASE "
                "(extended import - releases and tracks)"
            )
        else:
            self.cli.p(
                "Importing Discogs collection into DiscoBASE "
                "(regular import - just releases)"
            )

        releases = self.collection.me.collection_folders[0].releases
        total_releases = len(releases)

        with custom_progress as progress:
            task = progress.add_task("Processing releases...", total=total_releases)

            for item in releases:
                if offset and releases_processed < offset:
                    progress.update(task, advance=1)
                    releases_processed += 1
                    continue

                rel_created, d_artists, artists = self.create_release_entry(item)

                if not rel_created:
                    releases_db_errors += 1
                    log.error(
                        'importing release "%s" Continuing anyway.', item.release.title
                    )
                    progress.update(task, advance=1)
                    continue

                releases_added += 1

                if tracks:
                    tracks_count, db_errors, discogs_errors = self.process_tracks(
                        item.release.id, item.release.tracklist, d_artists
                    )
                    tracks_added += tracks_count
                    tracks_db_errors += db_errors
                    tracks_discogs_errors += discogs_errors

                msg_rel_add = f"Releases so far: {releases_added}"
                log.info(msg_rel_add)
                print(msg_rel_add)

                if tracks:
                    msg_trk_add = f"Tracks so far: {tracks_added}"
                    log.info(msg_trk_add)
                    print(msg_trk_add)

                print()  # leave some space after a release and all its tracks
                releases_processed += 1
                real_releases_processed += 1
                progress.update(task, advance=1)

        print(
            f"Processed releases: {releases_processed}. "
            f"Really processed releases: {real_releases_processed}. "
            f"Imported releases to DiscoBASE: {releases_added}."
        )
        print(f"Database errors (release import): {releases_db_errors}.")

        if tracks:
            print(
                f"Processed tracks: {tracks_processed}. "
                f"Imported tracks to DiscoBASE: {tracks_added}."
            )
            print(
                f"Database errors (track import): {tracks_db_errors}. "
                f"Discogs errors (track import): {tracks_discogs_errors}."
            )

        self.cli.duration_stats(start_time, "Discogs import")

    # Misc

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

    # Brainz fetchers and helpers

    def _err_cant_fetch(self, tr_no, rel_title):
        log.error(
            'Can\'t fetch "%s" on "%s". Either track number not valid on '
            "release or track not imported yet.",
            tr_no, rel_title,
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
                log.error('Track %s on "%s" (%s) not existing on Discogs (%s).',
                          d_track_no, discogs_title, d_release_id, HtErr)
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
                  'match detail option is: %s', detail)
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

            log.info('CTRL: Trying to match Discogs release %s "%s"...',
                     discogs_id, track['discogs_title'])
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
                log.warning(
                    'No Release MBID found for track %s on Discogs release "%s"',
                    track["d_track_no"],
                    track["discogs_title"],
                )
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
            if not track:
                self._err_cant_fetch(track_no.upper(), rel_id)
                return False
            tr_list = [track]

        return self.update_tracks_from_brainz(tr_list, detail)

    def edit_track(self, rel_id, rel_title, track_no):
        if not track_no:
            track_no = self.cli.ask_for_track(suggest = self.first_track_on_release)
        track_details = self.collection.get_track(rel_id, track_no.upper())
        if not track_details:
            self._err_cant_fetch(track_no, rel_title)
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
            return

        prettified_results = self.cli.replace_key_value_search_releases(search_results)
        self.cli.p('Found releases:')
        self.cli.tab_ls_releases(prettified_results)

    def import_sales_inventory(self):
        """Import sales inventory"""
        start_time = time()
        decode_err = other_err =  0
        self.cli.exit_if_offline(self.collection.ONLINE)
        self.cli.p("Importing Discogs sales inventory into DiscoBASE...")
        total_items = len(self.collection.me.inventory)

        with custom_progress:
            task = custom_progress.add_task(
                "[cyan] Status: ",
                total=total_items,
            )
            for listing in self.collection.me.inventory:
                try:
                    self.collection.create_sales_entry({
                        "d_sales_release_id": listing.release.id,
                        "d_sales_listing_id": listing.id,
                        "d_sales_release_url": listing.release.url,
                        "d_sales_url": listing.url,
                        "d_sales_condition": listing.condition,
                        "d_sales_sleeve_condition": listing.sleeve_condition,
                        "d_sales_price": str(listing.price.value),
                        "d_sales_comments": listing.comments,
                        "d_sales_allow_offers": 1 if listing.allow_offers else 0,
                        "d_sales_status": listing.status,
                        "d_sales_comments_private": listing.external_id,
                        "d_sales_counts_as": str(listing.format_quantity),
                        "d_sales_location": listing.location,
                        "d_sales_weight": str(listing.weight),
                        "d_sales_posted": datetime.strftime(listing.posted, "%Y-%m-%d"),
                    })
                    if listing.status == "Sold":
                        self.collection.toggle_sold_state(listing.release.id, True)
                    custom_progress.update(task, advance=1)
                except JSONDecodeError as e:
                    log.error("Catched a JSONDecodeError. Not retrying! %s", e)
                    decode_err += 1
                except Exception as e:
                    log.error("Catched an Exception. Not retrying! %s", e)
                    other_err += 1

        print(f"Discogs JSONDecode errors : {decode_err}.")
        print(f"Other errors : {other_err}.")
        self.cli.duration_stats(start_time, 'Inventory import')

    def import_sales_listing(self, listing_id):
        """Import a single marketplace listing."""
        listing, _, _ = self.collection.fetch_sales_listing_details(listing_id)
        listing["d_sales_listing_id"] = listing_id
        self.collection.create_sales_entry(listing)

    def tui_ls_releases(self, search_terms):
        """search_terms is a key value dict: eg: d_artist: artistname"""

        search_results = []
        self.cli.p('Searching database for: {}'.format(search_terms))

        try:
            search_results = self.collection.key_value_search_releases(
                search_key_value=search_terms,
                filter_cols=self.cli.cols_key_value_search.shortcuts_dict()
            )
        except Exception as error:
            self.cli.p(error)

        if not search_results:
            self.cli.p('Nothing found.')
            return

        prettified_results = self.cli.replace_key_value_search_releases(search_results)
        app = DiscodosListApp(
            rows=prettified_results,
            headers=self.cli.cols_key_value_search.headers_dict(),
            discogs=self.d,
            collection=self.collection,
            cli=self.cli,
        )
        app.run(inline=False)
        return

    def sell_record_wizard(
        self, query, release_id, condition, sleeve_condition, price, status, location,
        allow_offers, comments, private_comments,
    ):
        if not self.ONLINE:
            log.warning("Online mode is required to list a record for sale.")
            return

        if not release_id:
            found_release = self.search_release(" ".join(query))
            # search_release exits program, not required to handle here.
            release_id = found_release["id"]
        if not condition:
            condition = Prompt.ask(
                "Condition", choices=RECORD_CHOICES, default="VG+"
            )
        if not sleeve_condition:
            sleeve_condition = Prompt.ask(
                "Condition", choices=SLEEVE_CHOICES, default="generic"
            )

        prices, err_prices, _ = self.collection.fetch_relevant_price_suggestions(
            release_id, wanted_condition=condition
        )
        render_prices = (
            err_prices if err_prices else self.cli.two_column_view(prices, as_is=True)
        )
        print(Panel.fit(render_prices, title="Suggested prices"))

        stats, err_stats, _ = self.collection.fetch_marketplace_stats(release_id)
        render_stats = (
            err_stats if err_stats else self.cli.two_column_view(stats, as_is=True)
        )
        print(Panel.fit(render_stats, title="Marketplace stats"))

        print("Currently for sale:")
        print(f"https://www.discogs.com/sell/release/{release_id}")
        print()

        videos, err_videos, _ = self.collection.fetch_release_videos(release_id)
        render_videos = (
            err_videos if err_videos else self.cli.two_column_view(videos, as_is=True)
        )
        print(Panel.fit(render_videos, title="YouTube listen"))

        if not price:
            recommended_price = prices.get(condition)
            if recommended_price:
                print(
                    f"Suggested price for condition '{condition}': "
                    f"EUR {recommended_price}"
                )
                price = FloatPrompt.ask(
                    "Accept?",
                    default=recommended_price,
                )
            else:
                print("No suggested price available; please enter a price manually.")
                price = FloatPrompt.ask("Price")

        log.info(f"Attempting to list record {release_id} for sale.")
        listing_successful = self.collection.list_for_sale(
            release_id=release_id,
            condition=condition,
            sleeve_condition=sleeve_condition,
            price=price,
            status=status,
            location=location,
            allow_offers=allow_offers,
            comments=comments,
            private_comments=private_comments
        )
        if listing_successful:
            self.cli.p("Listed for sale.")
            last_added = self.me.inventory.sort("listed", Sort.Order.DESCENDING)
            self.import_sales_listing(last_added[0].id)
            self.cli.p("Imported listing to DiscoBASE.")

    def edit_sales_listing(self, listing_id, condition, sleeve_condition, price,
                           status, location, allow_offers, comments, private_comments):
        if not self.ONLINE:
            log.warning("Online mode is required to edit a Marketplace listing.")
            return

        details, err, _ = self.collection.fetch_sales_listing_details(listing_id)
        render_details = err if err else details
        print(
            Panel.fit(
                title="Current listing details",
                renderable=self.cli.two_column_view(
                   render_details
                ),
            )
        )

        edit_successful = self.collection.update_sales_listing(
            listing_id=listing_id,
            condition=condition,
            sleeve_condition=sleeve_condition,
            price=price,
            status=status,
            location=location,
            allow_offers=allow_offers,
            comments=comments,
            private_comments=private_comments,
        )
        if edit_successful:
            self.cli.p("Edited sales listing.")
            last_added = self.me.inventory.sort("listed", Sort.Order.DESCENDING)
            self.import_sales_listing(last_added[0].id)
            self.cli.p("Imported listing to DiscoBASE.")

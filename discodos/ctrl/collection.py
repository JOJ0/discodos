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
from rich.console import Console

from discodos.ctrl.common import ControlCommon
from discodos.model import Brainz
from discodos.model import Brainz_match
from discodos.model import Collection
from discodos.utils import is_number
from discodos.view import CollectionViewCommandline
from discodos.ctrl.tui import DiscodosListApp
from discodos.utils import (
    extract_discogs_id_regex,
    RECORD_CHOICES,
    SLEEVE_CHOICES,
    RECORD_CHOICES_DISCOGS,
    SLEEVE_CHOICES_DISCOGS,
    STATUS_CHOICES_DISCOGS,
    timestamp_now,
)

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
        self.app_id = appIdentifier
        self.user_token = userToken
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
        log.debug("CTRL: ONLINE=%s in %s", self.ONLINE, __class__.__name__)
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

    # Classic search

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

    # Import/remove single release/collection

    def orphane_collection_items(self, fetched_items, release_id):
        """Marks DiscoBASE collection items orphaned if not on Discogs anymore.

        fetched_items is a list of "Discogs collection item" dictionaries. Keys are as
        named in the Discogs object!

        release_id can be passed, so even if fetched_items is empty we can check for
        orphaned entries in DB.
        """
        db_items = self.collection.get_collection_items_by_release(release_id)
        d_instance_ids = [instance["instance_id"] for instance in fetched_items]
        for item in db_items:
            if (
                not item["d_coll_instance_id"] in d_instance_ids
                and not item["coll_orphaned"]
            ):
                log.warning(
                    "Marking orphaned: %s. Not in Discogs collection anymore.",
                    item["d_coll_instance_id"],
                )
                self.collection.set_collection_item_orphaned(item["d_coll_instance_id"])

    def add_release(self, release_id):
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)

        extracted_id = extract_discogs_id_regex(release_id)
        if not extracted_id:
            log.error('Not a valid Discogs release ID or URL')
            return False

        if self.collection.get_release_by_id(extracted_id):
            self.cli.p(
                "Release ID already in DiscoBASE, not adding to collection. "
                "We don't want dups!"
            )
            return False

        self.cli.p(f"Asking Discogs if release ID {extracted_id:d} is valid.")
        result = self.collection.fetch_discogs_release(extracted_id)
        if not result:
            log.debug("No Discogs release. Returning False.")
            self.cli.duration_stats(start_time, 'Adding Release to Collection')
            return False

        artists = self.collection.d_artists_to_str(result.artists)
        d_catno = self.collection.d_get_first_catno(result.labels)
        last_row_id = None

        self.cli.p(f'Adding "{result.title}" to collection')
        for folder in self.collection.me.collection_folders:
            if folder.id == 1:
                folder.add_release(extracted_id)
                last_row_id = self.collection.create_release(
                    result.id,
                    result.title,
                    artists,
                    d_catno,
                )
                coll_items = self.collection.fetch_collection_item_instances(
                    extracted_id
                )
                for instance in coll_items:
                    self.create_collection_item(
                        instance, sold_folder_id=self.user.conf.sold_folder_id
                    )
        if not last_row_id:
            self.cli.error_not_the_release()
        log.debug("Discogs release was maybe added to Collection")
        self.cli.duration_stats(start_time, 'Adding Release to Collection')
        return True

    def import_release(self, release_id):
        """Import a specific collection release into the DiscoBASE."""
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)

        with custom_progress as progress:
            task1 = progress.add_task("...",start=1, total=5)
            extracted_id = extract_discogs_id_regex(release_id)

            progress.console.print(f"Looking up {extracted_id:d} on Discogs")
            result = self.collection.fetch_discogs_release(extracted_id)
            progress.update(task1, advance=1)
            if not result:
                raise SystemExit(3)

            progress.console.print(f"Release ID is valid: {result.title}")
            progress.update(task1, advance=1)
            progress.console.print("Let's find it in your Discogs collection")
            coll_items = self.collection.fetch_collection_item_instances(extracted_id)
            if len(coll_items) < 1:
                progress.update(task1)
                log.warning("Not in collection. Use -a flag!")
                return
            release = coll_items[0]['full_instance'].release
            progress.update(task1, advance=1)

            if release:
                # Add release entry and collection entries
                self.create_release_entry(coll_items[0]["full_instance"].release)
                for instance in coll_items:
                    self.create_collection_item(
                        instance, sold_folder_id=self.user.conf.sold_folder_id
                    )
                # Check existing DB entries and mark orphaned if required
                self.orphane_collection_items(coll_items, extracted_id)
            else:
                self.cli.error_not_the_release()

            progress.update(task1, advance=1)
            self.cli.duration_stats(start_time, "Discogs import")
            progress.update(task1, completed=5)

    def remove_and_delete_release(self, release_id):
        """Remove all from collection and delete from DB."""
        extracted_id = extract_discogs_id_regex(release_id)
        coll_items = self.collection.fetch_collection_item_instances(extracted_id)

        for instance in coll_items:
            print(self.cli.two_column_view(instance))
            delete = Confirm.ask("Remove from Discogs collection?", default=False)
            if not delete:
                continue
            folder = self.collection.me.collection_folders[0]
            folder.remove_release(instance['full_instance'])

        if Confirm.ask("Show tracks in DiscoBASE to confirm removal?", default=False):
            tracks = self.collection.get_release_tracks_by_id(extracted_id)
            for track in tracks:
                print(
                    Panel.fit(
                        self.cli.two_column_view(track, as_is=True, skip_empty=True),
                        title=f"Track {track['d_track_no']}",
                    )
                )
            if len(tracks):
                if Confirm.ask("Remove release and tracks?", default=False):
                    self.collection.delete_release(extracted_id)
            else:
                print("No tracks. Moving on...")

            coll_items = self.collection.get_collection_items_by_release(extracted_id)
            for ci in coll_items:
                print(
                    Panel.fit(
                        self.cli.two_column_view(ci, as_is=True, skip_empty=True),
                        title=f"Collection item instance {ci['d_coll_instance_id']}",
                    )
                )
                sure_coll = Confirm.ask("Remove collection item?", default=False)
                if sure_coll:
                    self.collection.delete_collection_item(ci["d_coll_instance_id"])
                    continue
                else:
                    log.warning("Kept collection item in DiscoBASE!")
        return

    # Import collection, import helpers

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
                    # log.debug(msg_tr_add)
                    # print(msg_tr_add)
                else:
                    tracks_db_errors += 1
                    log.error("importing track. Continuing anyway.")
        except Exception as Exc:
            tracks_discogs_errors += 1
            log.error("Exception: %s", Exc)

        return tracks_added, tracks_db_errors, tracks_discogs_errors

    def create_release_entry(self, release):
        """Initiates adding a DiscoBASE release entry

        Expects a Discogs API Release object.

        Returns a tuple of (last_row_id, artists, catno) on success.
        """
        d_artists = release.artists
        artists = self.collection.d_artists_to_str(d_artists)
        first_catno = self.collection.d_get_first_catno(release.labels)
        self.print_release_info(release.id, artists, release.title)

        rel_created = self.collection.create_release(
            release.id, release.title, artists, first_catno,
        )

        return rel_created, d_artists, artists

    def create_collection_item(self, instance, sold_folder_id=None):
        """Creates a collection item by passing a dictionary to the DiscoBASE method."""
        value_f3 = self.cli.extract_collection_item_notes(instance)

        self.collection.create_collection_item(
            {
                "d_coll_instance_id": instance["instance_id"],
                "d_coll_release_id": instance["id"],
                "d_coll_folder_id": instance["folder_id"],
                "d_coll_added": instance["date_added"],
                "d_coll_rating": instance["rating"],
                "d_coll_notes": value_f3,
                "coll_sold": instance["folder_id"] == int(sold_folder_id),
                "coll_orphaned": 0,  # Temporary reset fix. FIXME
                "coll_mtime": timestamp_now(),
            }
        )

    def print_release_info(self, release_id, artists, title):
        print(f'Release {release_id} - "{artists}" - "{title}"')

    def import_collection(self, tracks=False, offset=0):
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)

        releases_processed = releases_added = releases_db_errors = 0
        tracks_processed = tracks_added = tracks_db_errors = tracks_discogs_errors = 0
        real_releases_processed = 0  # In case we start at offset, we need two counts
        imported_instance_ids = []  # After import we check for orphaned entries
        instances_orphaned = 0

        # Start tracks or basic import
        if tracks:
            self.cli.p(
                "Importing Discogs collection into DiscoBASE "
                "(extended import - releases and tracks)", trail_nl=False
            )
        else:
            self.cli.p(
                "Importing Discogs collection into DiscoBASE "
                "(regular import - just releases)", trail_nl=False
            )

        # Create/update collection folders
        folders = self.collection.me.collection_folders
        print("[i]Updating collection folder names...[/]", end=" ")
        folders = [
            {"d_collfolder_id": folder.id, "d_collfolder_name": folder.name}
            for folder in folders
        ]
        if not self.collection.create_collfolders(folders):
            log.error("Import failed.")
            return
        print("[i]Done.[/]")

        releases = self.collection.me.collection_folders[0].releases
        total_releases = len(releases)

        with custom_progress as progress:
            task = progress.add_task("Processing releases...", total=total_releases)

            for item in releases:
                if offset and releases_processed < offset:
                    progress.update(task, advance=1)
                    releases_processed += 1
                    continue

                imported_instance_ids.append(item.instance_id)
                rel_created, d_artists, _ = self.create_release_entry(item.release)
                self.create_collection_item(
                    item.data,
                    sold_folder_id=self.user.conf.sold_folder_id,
                )

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
                # Just log, don't print, user sees progress bar

                if tracks:
                    msg_trk_add = f"Tracks so far: {tracks_added}"
                    log.info(msg_trk_add)
                    print(msg_trk_add)

                releases_processed += 1
                real_releases_processed += 1
                progress.update(task, advance=1)

        # Final cleanup
        print("Looking for orphaned collection items...")
        for item in self.collection.get_all_collection_items():
            if (
                not item["d_coll_instance_id"] in imported_instance_ids
                and not item["coll_orphaned"]
            ):
                instances_orphaned += 1
                log.warning(
                    "Marking orphaned: %s. Not in Discogs collection anymore.",
                    item["d_coll_instance_id"],
                )
                self.collection.set_collection_item_orphaned(item["d_coll_instance_id"])

        # Final report
        report_notes = {
            "Processed releases": releases_processed,
            "Actually processed releases": real_releases_processed,
            "Imported releases to DiscoBASE": releases_added,
            "Marked orphaned collection items": instances_orphaned,
            "Database errors (release import)": releases_db_errors,
        }
        if tracks:
            report_notes.update({
                    "Processed tracks": tracks_processed,
                    "Imported tracks to DiscoBASE": tracks_added,
                    "Database errors (track import)": tracks_db_errors,
                    "Discogs errors (track import)": tracks_discogs_errors,
                })
        print(
            Panel.fit(
                self.cli.two_column_view(report_notes, as_is=True),
                title="Final report",
            )
        )
        self.cli.duration_stats(start_time, "Discogs import")

    # Suggest

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

    # Tracks/Brainz

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
            full_release = self.collection.fetch_discogs_release(rel_id)
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
            d_rel = self.collection.fetch_discogs_release(discogs_id) # 404 is handled here

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
            full_release = self.collection.fetch_discogs_release(rel_id)
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

    # Misc

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
            self.collection.stats_collection_items_discobase(),
            self.collection.stats_collection_items_discogs(),
            self.collection.stats_sales_listings_discobase(),
            self.collection.stats_sales_listings_discogs(),
            self.collection.stats_sales_listings_forsale(),
            self.collection.stats_sales_listings_sold(),
            self.collection.stats_mixtracks_total(),
            self.collection.stats_mixtracks_unique(),
            self.collection.stats_tracks_key_brainz(),
            self.collection.stats_tracks_key_manual(),
            self.collection.stats_tracks_bpm_brainz(),
            self.collection.stats_tracks_bpm_manual(),
        )

    # Sales import

    def print_import_sales_notes(self):
        print(
            "[cyan]"
            "- Adds missing data for non-collection releases.\n"
            "- Marks draft sales entries as sold when location comments match "
            "configured pattern.\n"
            # Disabled for now, patched out manual sold toggle
            # "- Additionally tries to match collection items and marks them as sold.\n"
            # "- To manually set sold flag, use `dsc ls id=<id>` with 'Toggle sold' "
            # "command (s).\n"
            "[/]"
        )

    def is_listing_sold(self, listing_status, listing_location):
        """Returns for database import already."""
        if (
            listing_status.lower() == "sold"
            or "verkauft" in listing_location.lower()
            or "verschenkt" in listing_location.lower()
            or "geschenkt" in listing_location.lower()
        ):
            return 1
        return 0

    def handle_listing_release_and_sold_flag(
        self, release_id, listing_status, listing_location, listing_id=None
    ):
        """Postprocess sales listing imports.

        - Create missing release record
        - Update collection sold flag

        Expects a sales listing object.
        """
        # Check if release info is available; fetch details and create entry if not.
        if not self.collection.get_release_by_id(release_id):
            log.info("Fetching release details for sales listing.")
            self.create_release_entry(
                self.collection.fetch_discogs_release(release_id)
            )

        # Disabled for now:
        # - Manual sales toggle patched out.
        # - Unsure about auto-assiging first collection item
        # - For now, manually moving to designated folder is most straight-forward
        #
        # # Set sold flag on single collection items. Inform if decision not possible.
        # is_sold = self.is_listing_sold(listing_status, listing_location)
        # if is_sold == 1:
        #     toggled, details = self.collection.toggle_collection_sold_flag(
        #         release_id, True, listing_id=listing_id
        #     )
        #     if not toggled:
        #         custom_progress.console.print(
        #             "[yellow]Multiple instances in collection. "
        #             f"Mark sold manually: {details}[/]"
        #         )

    def import_sales_inventory(self, light_import=False):
        """Import sales inventory"""
        start_time = time()
        decode_err = other_err =  0
        self.cli.exit_if_offline(self.collection.ONLINE)
        self.cli.p("Importing Discogs sales inventory into DiscoBASE...")
        self.print_import_sales_notes()
        total_items = len(self.collection.me.inventory)

        with custom_progress:
            task = custom_progress.add_task(
                "[cyan] Status: ",
                total=total_items,
            )
            for listing in self.collection.me.inventory:
                try:
                    if light_import:
                        self.collection.create_sales_entry({
                            "d_sales_listing_id": listing.id,
                            "d_sales_release_id": listing.release.id,
                            "d_sales_status": STATUS_CHOICES_DISCOGS[listing.status],
                            "d_sales_allow_offers": 1 if listing.allow_offers else 0,
                            "d_sales_posted": datetime.strftime(listing.posted, "%Y-%m-%d"),  # pylint: disable=C0301
                        })
                    else:
                        self.collection.create_sales_entry({
                            "d_sales_listing_id": listing.id,
                            "d_sales_release_id": listing.release.id,
                            "d_sales_release_url": self.cli.link_to(
                                "discogs release", listing.release.id
                            ),
                            "d_sales_url": listing.url,
                            "d_sales_condition": RECORD_CHOICES_DISCOGS[listing.condition],
                            "d_sales_sleeve_condition": SLEEVE_CHOICES_DISCOGS[listing.sleeve_condition],
                            "d_sales_price": str(listing.price.value),
                            "d_sales_comments": listing.comments,
                            "d_sales_allow_offers": 1 if listing.allow_offers else 0,
                            "d_sales_status": STATUS_CHOICES_DISCOGS[listing.status],
                            "d_sales_comments_private": listing.external_id,
                            "d_sales_counts_as": str(listing.format_quantity),
                            "d_sales_location": listing.location,
                            "d_sales_weight": str(listing.weight),
                            "d_sales_posted": datetime.strftime(listing.posted, "%Y-%m-%d"),
                            "sales_sold": self.is_listing_sold(
                                listing.status,
                                listing.location
                            ),
                        })
                    # Handle missing release info and toggle collection sold flag.
                    self.handle_listing_release_and_sold_flag(
                        listing.release.id,
                        listing.status,
                        listing.location,
                        listing_id=listing.id,
                    )
                except JSONDecodeError as e:
                    log.error("Sales import JSONDecodeError. Not retrying! %s", e)
                    decode_err += 1
                except Exception as e:
                    log.error("Sales import Exception. Not retrying! %s", e)
                    other_err += 1
                custom_progress.update(task, advance=1)

        print(f"Discogs JSONDecode errors : {decode_err}.")
        print(f"Other errors : {other_err}.")
        self.cli.duration_stats(start_time, 'Inventory import')

    def import_sales_listing(self, listing_id, display_help=False):
        """Import a single marketplace listing."""
        if display_help:
            self.print_import_sales_notes()
        listing, err, _ = self.collection.fetch_sales_listing_details(listing_id)
        if err:
            self.cli.p("Listing not existing.")
            return
        listing["d_sales_listing_id"] = listing_id  # fetch doesn't have ID.
        # Append sales_sold field
        listing["sales_sold"] = self.is_listing_sold(
            listing["d_sales_status"],
            listing["d_sales_location"],
        )
        self.collection.create_sales_entry(listing)
        # Handle missing release info and toggle collection sold flag.
        self.handle_listing_release_and_sold_flag(
            listing["d_sales_release_id"],
            listing["d_sales_status"],
            listing["d_sales_location"],
            listing_id=listing["d_sales_listing_id"],
        )
        self.cli.p("Sales listing import done.")

    def remove_and_delete_sales_listing(self, listing_id):
        """Remove all from collection and delete from DB."""

        listing, err, edetails = self.collection.fetch_sales_listing_details(listing_id)
        if err:
            print(err, edetails)
        if listing:
            print(self.cli.two_column_view(listing))
            if Confirm.ask("Remove from Discogs Marketplace inventory?", default=False):
                self.collection.remove_sales_listing(listing_id)

        listing_db = self.collection.get_sales_listing_details(listing_id)
        if not listing_db:
            self.cli.p("Listing not in DiscoBASE.")
            return

        print(
            Panel.fit(
                self.cli.two_column_view(listing_db, as_is=True, skip_empty=True),
                title=f"Listing {listing_id}",
            )
        )
        sure = Confirm.ask("Delete in DiscoBASE?", default=False)
        if sure:
            self.collection.delete_sales_inventory_item(listing_id)
            return

        log.warning("Kept sales listing in DiscoBASE!")
        return

    # ls, ls TUI, links

    def prepare_key_value_search(self, query):
        """Returns a dictionary from space-delimited key=value pairs."""
        kv = {}
        non_kv = []
        for item in query:
            if "=" in item:
                key, value = item.split("=")
                kv[key] = value
            else:
                non_kv.append(item)

        if non_kv:
            if not kv:
                kv = {"title": "%".join(non_kv)}
            elif "title" in kv:
                kv_title = kv["title"].replace(" ", "%")
                non_kv_terms = "%".join(non_kv)
                kv["title"] = f"{kv_title}%{non_kv_terms}"
            else:
                kv["title"] = "%".join(non_kv)
        return kv

    def tui_ls_releases(
        self, search_terms, orderby=None, reverse_order=False, sales_extra=False, limit=None
    ):
        """search_terms is a key value dict: eg: d_artist: artistname"""

        search_results = None
        self.cli.p('Searching database for: {}'.format(search_terms))
        # Replace orderby with proper database key
        if self.cli.cols_key_value_search.shortcuts_dict().get(orderby):
            orderby = self.cli.cols_key_value_search.shortcuts_dict()[orderby]

        try:
            search_results = self.collection.key_value_search_releases(
                search_key_value=search_terms if search_terms else {},
                orderby=orderby,
                reverse_order=reverse_order,
                filter_cols=self.cli.cols_key_value_search.shortcuts_dict(),
                sales_extra=sales_extra,
                limit=limit,
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
            sales_listing_headers=self.cli.cols_sales_listing_details.headers_dict(),
            discogs=self.d,
            collection=self.collection,
            cli=self.cli,
            user=self.user,
        )
        app.run(inline=False)
        return

    def ls_releases(
        self, search_terms, orderby=None, reverse_order=False, sales_extra=False, limit=None
    ):
        """search_terms is a key value dict: eg: d_artist: artistname"""

        search_results = []
        self.cli.p('Searching database for: {}'.format(search_terms))
        # Replace orderby with proper database key
        if self.cli.cols_key_value_search.shortcuts_dict().get(orderby):
            orderby = self.cli.cols_key_value_search.shortcuts_dict()[orderby]
        try:
            search_results = self.collection.key_value_search_releases(
                search_key_value=search_terms,
                orderby=orderby,
                reverse_order=reverse_order,
                filter_cols=self.cli.cols_key_value_search.shortcuts_dict(),
                sales_extra=sales_extra,
                limit=limit,
            )
        except Exception as error:
            self.cli.p(error)

        if not search_results:
            self.cli.p('Nothing found.')
            return

        prettified_results = self.cli.replace_key_value_search_releases(search_results)
        prettified_results = self.cli.trim_table_fields(prettified_results)
        self.cli.p('Found releases:')
        self.cli.tab_ls_releases(prettified_results)

    def view_links_list(self, query, orderby):
        releases = None
        # Replace orderby with proper database key
        if self.cli.cols_key_value_search.shortcuts_dict().get(orderby):
            orderby = self.cli.cols_key_value_search.shortcuts_dict()[orderby]
        # Fetch from DiscoBASE
        try:
            releases = self.collection.key_value_search_releases(
                search_key_value=query if query else {},
                orderby=orderby,
                filter_cols=self.cli.cols_key_value_search.shortcuts_dict(),
                custom_fields=[
                    "d_catno",
                    "d_artist",
                    "discogs_title",
                    "discogs_id",
                    "m_rel_id",
                    "m_rel_id_override",
                    "d_sales_listing_id"
                ],
            )
        except Exception as error:
            self.cli.p(error)

        # Nothing and exit
        if not releases:
            self.cli.p('Nothing found.')
            return
        # Display
        self.cli.tab_all_releases(releases)

    # Sell

    def sell_record_wizard(  # pylint: disable=too-many-locals
        self, query, release_id, condition, sleeve_condition, price, status, location,
        allow_offers, comments, comments_private,
    ):
        if not self.ONLINE:
            log.warning("Online mode is required to list a record for sale.")
            return

        extracted_id = None
        if release_id:
            extracted_id = extract_discogs_id_regex(release_id)

        if not extracted_id:
            found_release = self.search_release(" ".join(query))
            # search_release exits program, not required to handle here.
            extracted_id = found_release["id"]
        if not condition:
            condition = Prompt.ask(
                "Condition", choices=RECORD_CHOICES, default="VG+"
            )
        if not sleeve_condition:
            sleeve_condition = Prompt.ask(
                "Sleeve Condition", choices=SLEEVE_CHOICES, default="generic"
            )

        prices, err_prices, _ = self.collection.fetch_relevant_price_suggestions(
            extracted_id, wanted_condition=condition
        )
        render_prices = (
            err_prices if err_prices else self.cli.two_column_view(prices, as_is=True)
        )
        print(Panel.fit(render_prices, title="Suggested prices"))

        stats, err_stats, _ = self.collection.fetch_marketplace_stats(extracted_id)
        render_stats = (
            err_stats if err_stats else self.cli.two_column_view(stats, as_is=True)
        )
        print(Panel.fit(render_stats, title="Marketplace stats"))

        print("Currently for sale:")
        print(f"https://www.discogs.com/sell/release/{extracted_id}")
        print()

        videos, err_videos, _ = self.collection.fetch_release_videos(extracted_id)
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

        log.info(f"Attempting to list record {extracted_id} for sale.")
        listing_successful = self.collection.list_for_sale(
            release_id=extracted_id,
            condition=condition,
            sleeve_condition=sleeve_condition,
            price=price,
            status=status,
            location=location,
            allow_offers=allow_offers,
            comments=comments,
            comments_private=comments_private
        )
        if listing_successful:
            self.cli.p("Listed for sale.")
            last_added = self.me.inventory.sort("listed", Sort.Order.DESCENDING)
            self.import_sales_listing(last_added[0].id)
            self.cli.p(f"Imported listing {last_added[0].id} to DiscoBASE.")

    def edit_sales_listing(self, listing_id, condition, sleeve_condition, price,
                           status, location, allow_offers, comments, comments_private):
        if not self.ONLINE:
            log.warning("Online mode is required to edit a Marketplace listing.")
            return

        details, err, _ = self.collection.fetch_sales_listing_details(
            listing_id, db_keys=False)
        current_details = err if err else details
        print(
            Panel.fit(
                title="Current listing details",
                renderable=self.cli.two_column_view(current_details),
            )
        )
        new_details = {
            "listing_id": listing_id,
            "condition": condition,
            "sleeve_condition": sleeve_condition,
            "price": price,
            "status": status,
            "location": location,
            "allow_offers": allow_offers,
            "comments": comments,
            "comments_private": comments_private,  # we fetched with this key from db
        }
        updated_details = new_details
        updated_details = {
            **new_details,
            **{
                key: current_details[key]
                for key, value in new_details.items()
                if value is None
            },
        }
        print(
            Panel.fit(
                title="Proposed listing details",
                renderable=self.cli.two_column_view(updated_details),
            )
        )
        if not Confirm.ask(prompt="Update?", show_choices=True, default=False):
            return

        edit_successful = self.collection.update_sales_listing(**updated_details)
        if edit_successful:
            self.cli.p("Edited sales listing.")
            last_added = self.me.inventory.sort("listed", Sort.Order.DESCENDING)
            self.import_sales_listing(last_added[0].id)
            self.cli.p(f"Imported listing {last_added[0].id} into DiscoBASE.")

    # Cleanup

    def cleanup_sales_inventory(self, offset=0):
        """Cleanup sales inventory"""
        start_time = time()
        orphaned_entries =  0
        self.cli.exit_if_offline(self.collection.ONLINE)
        self.cli.p("Cleaning up DiscoBASE sales inventory...")
        total_items = self.collection.stats_sales_items_total()
        sales = self.collection.get_sales_inventory(offset)

        console = Console()
        adapted_progress = Progress(
            MofNCompleteColumn(),
            BarColumn(),
            TaskProgressColumn(),
        )
        with adapted_progress:
            task = adapted_progress.add_task(
                "[cyan] Status: ",
                completed=offset,
                total=total_items,
            )
            for row in sales:
                existing = self.collection.fetch_sales_listing_ok(
                    row["d_sales_listing_id"]
                )
                if not existing:
                    orphaned_entries += 1
                    console.print(row)
                    self.collection.delete_sales_inventory_item(
                        row["d_sales_listing_id"]
                    )
                    console.print(
                        "[yellow]Listing not on Discogs anymore. Deleted.[/]"
                    )
                adapted_progress.update(task, advance=1)

        print(f"Orphaned entries deleted: {orphaned_entries}.")
        self.cli.duration_stats(start_time, 'Sales inventory cleanup')

    def cleanup_releases(self, offset=0):
        """Cleanup the release table. Remove orphaned entries.

        Orphaned means: Not used by `sales`, `mixes` or `collection` features
        anymore.
        """
        start_time = time()
        orphaned_entries =  0
        self.cli.exit_if_offline(self.collection.ONLINE)
        self.cli.p("Cleaning up the DiscoBASE release table...")
        # total_items = self.collection.stats_releases_total()
        collection = self.collection.get_all_db_releases(offset, as_dict=True)

        print(
            "The following releases are not used in any [yellow]sales listing, mix or "
            "collection item[/] and can be safely deleted:\n"
        )
        for row in collection:
            coll_existing = self.collection.get_collection_items_by_release(
                row["discogs_id"],
                quiet=True,
            )
            listing_existing = self.collection.get_sales_listings_by_release(
                row["discogs_id"],
                quiet=True,
            )
            mix_tracks_existing = self.collection.get_mix_tracks_by_release(
                row["discogs_id"],
                quiet=True,
            )
            if (
                not coll_existing
                and not listing_existing
                and not mix_tracks_existing
            ):
                orphaned_entries += 1
                entry = " - ".join([str(value) for value in row.values()])
                print(f"\n{entry}")
                print(self.cli.link_to("discogs release", row["discogs_id"]))
                confirm = Confirm.ask("Delete?", default=False)
                if confirm:
                    self.collection.delete_release(row["discogs_id"])

        print(f"Orphaned entries found: {orphaned_entries}.")
        self.cli.duration_stats(start_time, 'Release table cleanup')

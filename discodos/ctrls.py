from discodos.utils import is_number
from discodos.config import Db_setup
from discodos.models import Mix, Collection, Brainz, Brainz_match
from discodos.views import Mix_view_cli, Collection_view_cli
from abc import ABC
import logging
import discogs_client.exceptions as errors
import pprint as p
from time import time

log = logging.getLogger('discodos')


class Ctrl_common (ABC):
    def __init__(self):
        pass

    def setup_db(self, db_file):
        db_setup = Db_setup(db_file)
        db_setup.create_tables()
        db_setup.upgrade_schema()


# mix controller class (abstract) - common attrs and methods  for gui and cli
class Mix_ctrl_common (ABC):
    def __init__(self):
        pass


# mix controller class CLI implementation
class Mix_ctrl_cli (Ctrl_common, Mix_ctrl_common):

    def __init__(self, db_conn, mix_name_or_id, _user_int, db_file = False):
        self.user = _user_int # take an instance of the User_int class and set as attribute
        self.cli = Mix_view_cli() # instantiatie the Mix view class (the CLI)
        self.mix = Mix(db_conn, mix_name_or_id, db_file) # instantiate the Mix model class
        if self.mix.db_not_found == True:
            self.cli.ask('Setting up DiscoBASE, press enter...')
            super(Mix_ctrl_cli, self).setup_db(db_file)
            self.mix = Mix(db_conn, db_file)

    def create(self):
        if is_number(self.mix.name_or_id):
            log.error("Mix name can't be a number!")
        else:
            if self.mix.name_existing:
                log.error('Mix "{}" already existing.'.format(self.mix.name))
                raise SystemExit(1)
            self.cli.p('Creating new mix "{}".'.format(self.mix.name))
            answers = self._create_ask_details()
            created_id = self.mix.create(answers['played'], answers['venue'])
            self.cli.p('New mix created with ID {}.'.format(created_id))
            self.view_mixes_list()

    def _create_ask_details(self):
        played = self.cli.ask("When did you (last) play it? eg 2018-01-01 ")
        venue = self.cli.ask(text="And where? ")
        return {'played': played, 'venue': venue}

    def view_mixes_list(self):
        ''' view a list of all mixes '''
        mixes_data = self.mix.get_all_mixes(order_by='played DESC')
        #mixes_data = self.mix.get_all_mixes(order_by='venue, played DESC')
        self.cli.tab_mixes_list(mixes_data)

    def view(self):
        if self.mix.id_existing:
            self.cli.tab_mix_info_header(self.mix.get_mix_info())
            if self.user.WANTS_VERBOSE_MIX_TRACKLIST:
                full_mix = self.mix.get_full_mix(verbose=True, order_by=self.user.MIX_SORT)
            elif self.user.WANTS_MUSICBRAINZ_MIX_TRACKLIST:
                full_mix = self.mix.get_full_mix(brainz=True, order_by=self.user.MIX_SORT)
            else:
                full_mix = self.mix.get_full_mix(verbose=False, order_by=self.user.MIX_SORT)

            if not full_mix:
                self.cli.p("No tracks in mix yet.")
            else:
                if self.user.WANTS_VERBOSE_MIX_TRACKLIST:
                    self.cli.tab_mix_table(full_mix, _verbose = True)
                elif self.user.WANTS_MUSICBRAINZ_MIX_TRACKLIST:
                    self.cli.tab_mix_table(full_mix, brainz = True)
                else:
                    self.cli.tab_mix_table(full_mix, _verbose = False)
        else:
            self.cli.p("Mix \"{}\" is not existing yet!".format(self.mix.name_or_id))

    def delete(self):
        if self.mix.id_existing:
            if self.cli.really_delete_mix(self.mix.id, self.mix.name):
                if self.mix.delete():
                    self.cli.p(
                      'Mix "{} - {}" deleted successfully.'.format(
                          self.mix.id, self.mix.name))
        else:
           self.cli.p("Mix \"{}\" doesn't exist.".format(self.mix.name_or_id))

    def edit_track(self, edit_track):
        if self.mix.id_existing:
            msg_editing ='Editing track {} in "{}".\n'.format(edit_track, self.mix.name)
            msg_editing+='* to keep a value as is, press enter\n'
            msg_editing+='* text in (braces) shows current value'
            self.cli.p(msg_editing)
            track_details = self.mix.get_one_mix_track(edit_track)
            if track_details:
                self.cli.p("{} - {} - {}".format(
                           track_details['discogs_title'],
                           track_details['d_track_no'],
                           track_details['d_track_name']))
                log.info("current d_release_id: %s", track_details['d_release_id'])
                edit_answers = self.cli.edit_ask_details(track_details,
                        self.cli._edit_track_questions)
                for a in edit_answers.items():
                    log.info("answers: %s", str(a))
                update_ok = self.mix.update_mix_track_and_track_ext(track_details, edit_answers)
                if update_ok:
                    self.cli.p("Track edit was successful.")
                else:
                    log.error("Something went wrong on mix_track edit!")
                    raise SystemExit(1)
                self.view()
            else:
                self.cli.p("No track "+edit_track+" in \""+
                            self.mix.name+"\".")
        else:
            self.cli.p("Mix unknown: \"{}\".".format(self.mix.name_or_id))

    def edit_mix(self):
        if self.mix.id_existing:
            msg_editing ='Editing mix {}\n'.format(self.mix.name)
            msg_editing+='* to keep a value as is, press enter\n'
            msg_editing+='* text in (braces) shows current value'
            self.cli.p(msg_editing)
            mix_details = self.mix.get_mix_info()
            if mix_details:
                self.cli.p("{} - {} - {}".format(
                           mix_details['name'],
                           mix_details['played'],
                           mix_details['venue']))
                edit_answers = self.cli.edit_ask_details(mix_details,
                        self.cli._edit_mix_questions)
                check_name = None
                for key,a in edit_answers.items():
                    log.info("answers: %s:%s", key, str(a))
                    if key == 'name':
                        check_name = self.mix._get_mix_id(a)
                if check_name != None:
                    log.warning("Name already taken. Dropping name-edit from update.")
                    del(edit_answers['name'])
                update_ok = self.mix.update_mix_info(mix_details, edit_answers)
                if update_ok:
                    self.cli.p("Mix edit was successful.")
                else:
                    log.error("Something went wrong on mix edit!")
                    raise SystemExit(1)
                # on dup-name err, don't show mixes list, user should see warning
                if check_name == None:
                    self.view_mixes_list()
            else:
                self.cli.p("Mix details couldn't be fetched.")
        else:
            self.cli.p('Mix unknown: "{}".'.format(self.mix.name_or_id))

    def bulk_edit_tracks(self, fields_str, first_track):
        log.debug("bulk_edit_tracks args: {} {}".format(fields_str, first_track))
        fields_list = fields_str.split(',')
        log.debug('fields split: {}'.format(fields_list))
        if not first_track:
            first_track = 1
        if self.mix.id_existing:
            for track in self.mix.get_full_mix(verbose = True):
                if not track['track_pos'] < first_track:
                    self.cli.p(
                           "Editing track {}  |  {} - {}  |  {} - {}".format(
                           track['track_pos'], track['discogs_title'], track['d_track_no'],
                           track['d_artist'], track['d_track_name']))
                    track_details = self.mix.get_one_mix_track(track['track_pos'])
                    bulk_questions = []
                    for field in fields_list:
                        #field=field.replace('d_', '')
                        #log.info("checking field: {}".format(field))
                        for question in self.cli._edit_track_questions:
                            if field == question[0]:
                                #log.info("appending to bulk_questions list")
                                bulk_questions.append(question)
                    log.debug("CTRL: bulk_questions: {}".format(bulk_questions))
                    edit_answers = self.cli.edit_ask_details(track_details,
                        bulk_questions)
                    self.mix.update_mix_track_and_track_ext(track_details,
                          edit_answers)
                    print("") # just some space

    def reorder_tracks(self, startpos = 1):
        reordered = self.mix.reorder_tracks(int(startpos))
        if not reordered:
            log.error("Reorder failed. No track {} in mix.".format(startpos))
        else:
            log.info("Reordering tracks successful")
            self.view()

    def delete_track(self, delete_track_pos):
        if self.cli.really_delete_track(delete_track_pos, self.mix.name):
             successful = self.mix.delete_track(delete_track_pos)
             # reorder existing and print tracklist
             if successful:
                 if delete_track_pos == 1:
                    self.mix.reorder_tracks(1)
                 else:
                    self.mix.reorder_tracks(delete_track_pos - 1)
                 self.view()
             else:
                 self.cli.p("Delete failed, maybe nonexistent track position?")

    # definitely cli specific

    def add_offline_track(self, rel_list, track_no, pos):
        if rel_list:
            self._add_track(rel_list[0][0], rel_list[0][1], track_no, pos)

    def add_discogs_track(self, release_details, track_no, pos, track_no_suggest = ''):
        log.info("add_discogs_track got this release_details: {}".format(
          release_details))
        if release_details:
            if not track_no:
                track_no = self.cli.ask_for_track(suggest = track_no_suggest)
            self._add_track(release_details['id'], release_details['title'],
              track_no, pos)
        else:
            log.error("No release to add to mix.")

    # _add_track should only be called from add_offline_track() and add_discogs_track()
    def _add_track(self, _release_id, _release_title, _track_no, _pos):
        if not _track_no:
            track_to_add = self.cli.ask_for_track()
        else:
            log.debug("_track_no was given, value is {}".format(_track_no))
            track_to_add = _track_no
        if _pos == None:
            log.debug("_pos was None, setting to 0")
            _pos = 0
        log.debug("This is _pos: {}".format(_pos))
        log.debug("This is track_to_add: {}".format(track_to_add))
        log.debug("This is _release_id: %s", _release_id)
        log.debug("This is _release_title: %s", _release_title)
        if self.mix.id_existing:
            last_track = self.mix.get_last_track()
            log.debug("Currently last track in mix is: %s", last_track[0])
            current_id = False
            if _pos:
                # a position to squeeze in the track was given
                # get current tracks >= pos
                tracks_to_shift = self.mix.get_tracks_from_position(_pos)
                if self.cli.really_add_track(track_to_add, _release_title,
                                             self.mix.id, _pos):
                    current_id = self.mix.add_track(_release_id,
                                                    track_to_add, track_pos = _pos)
                    # all good? reorder tracks
                    if current_id:
                        log.info("Add track to mix successful, now reordering ...")
                        self.mix.reorder_tracks_squeeze_in(_pos, tracks_to_shift)
                else:
                    print("Track not added.")
                    return True
            elif is_number(last_track[0]):
                # no position was given, tracks already mix
                if self.cli.really_add_track(track_to_add, _release_title,
                                             self.mix.id, last_track[0]+1):

                    current_id = self.mix.add_track(_release_id,
                                                    track_to_add, track_pos = last_track[0] + 1)
                else:
                    print("Track not added.")
                    return True
            else:
                # no position and it's the first track ever added
                if self.cli.really_add_track(track_to_add, _release_title,
                                             self.mix.id, 1):

                    current_id = self.mix.add_track(_release_id,
                                                    track_to_add, track_pos = 1)
                else:
                    print("Track not added.")
                    return True
            # FIXME untested if this is actually a proper sanity check
            log.debug("Value of current_id in add_offline_track: {}".format(current_id))
            if current_id:
                self.view()
                #return True
            else:
                log.error("Add track to DB failed!")
                #return False
        else:
            self.cli.p("Mix ID {} is not existing yet.".format(self.mix.id))
            return False

    def pull_track_info_from_discogs(self, coll_ctrl, start_pos=0,
          offset=0):
        if not coll_ctrl.ONLINE:
            self.cli.p("Not online, can't pull from Discogs...")
            return False # exit method we are offline

        if self.mix.id_existing:
            self.cli.p(
             "Let's update current mixes tracks with info from Discogs...")
            mixed_tracks = self.mix.get_mix_tracks_for_brainz_update(start_pos)
        else:
            self.cli.p(
             "Let's update every track contained in any mix with info from Discogs...")
            mixed_tracks = self.mix.get_all_mix_tracks_for_brainz_update(offset)

        if offset:
            update_ret = coll_ctrl.update_tracks_from_discogs(mixed_tracks,
              offset)
        else:
            update_ret = coll_ctrl.update_tracks_from_discogs(mixed_tracks,
              start_pos)

        return update_ret

    def update_track_info_from_brainz(self, coll_ctrl, start_pos=0,
          detail=1, offset=0):
        if not coll_ctrl.ONLINE:
            self.cli.p("Not online, can't pull from AcousticBrainz...")
            return False # exit method we are offline

        if self.mix.id_existing:
            self.cli.p(
             "Let's update current mixes tracks with info from AcousticBrainz...")
            mixed_tracks = self.mix.get_mix_tracks_for_brainz_update(
              start_pos)
        else:
            self.cli.p(
             "Let's update every track contained in any mix with info from AcousticBrainz...")
            mixed_tracks = self.mix.get_all_mix_tracks_for_brainz_update(
              offset)

        if offset:
            match_ret = coll_ctrl.update_tracks_from_brainz(mixed_tracks,
              detail, offset)
        else:
            match_ret = coll_ctrl.update_tracks_from_brainz(mixed_tracks,
              detail, start_pos)

        return match_ret

    def copy_mix(self):
        self.cli.p("Copying mix {} - {}.".format(self.mix.id, self.mix.name))
        copy_tr = self.mix.get_tracks_of_one_mix()
        new_mix_name = self.cli.ask("How should the copy be named? ")
        new_mix = Mix(self.mix.db_conn, new_mix_name)
        db_return_new = new_mix.create(self.mix.played, self.mix.venue, new_mix_name)
        if db_return_new:
            for tr in copy_tr:
                log.debug("CTRL copy_mix data: {}, {}, {}, {}, {}, ".format(
                    tr["d_release_id"], tr["d_track_no"], tr["track_pos"], tr["trans_rating"],
                    tr["trans_notes"]))
                new_mix.add_track(tr["d_release_id"], tr["d_track_no"], tr["track_pos"], tr["trans_rating"],
                    tr["trans_notes"])
            new_mix.db_conn.commit()
            self.cli.p("Copy mix successful. New ID is {}.".format(new_mix.id))
            return True
        else:
            log.error("Copy mix failed. Couldn't create.")
            return False

    def update_in_d_coll(self, coll_ctrl, start_pos = False):
        if coll_ctrl.ONLINE:
            if self.mix.id_existing:
                self.cli.p("Let's update Discogs collection field in current mixes releases...")
                #db_releases = self.mix.get_releases_of_one_mix(start_pos)
                #for db_rel in db_releases:
                #    pass
            #else:
            #    self.cli.p("Let's update ALL tracks in ALL mixes with info from Discogs...")
            #    mixed_tracks = self.mix.get_all_tracks_in_mixes()


# Collection controller common methods
class Coll_ctrl_common (ABC):
    def __init__(self):
        pass


# Collection controller class
class Coll_ctrl_cli (Ctrl_common, Coll_ctrl_common):
    '''manages the record collection, offline and with help of discogs data'''

    def __init__(self, _db_conn, _user_int, _userToken, _appIdentifier,
            _db_file = False, _musicbrainz_user = False, _musicbrainz_pass = False):
        self.user = _user_int # take an instance of the User_int class and set as attribute
        self.cli = Collection_view_cli() # instantiate cli frontend class 
        self.collection = Collection(_db_conn, _db_file)
        if self.collection.db_not_found == True:
            self.cli.ask('Setting up DiscoBASE, press enter...')
            super(Coll_ctrl_cli, self).setup_db(_db_file)
            self.collection = Collection(_db_conn, _db_file)
        if self.user.WANTS_ONLINE:
            if not self.collection.discogs_connect(_userToken, _appIdentifier):
                log.error("connecting to Discogs API, let's stay offline!\n")
            else: # only try to initialize brainz if discogs is online already
                self.brainz = Brainz(_musicbrainz_user, _musicbrainz_pass, _appIdentifier)
        log.info("CTRL: Initial ONLINE status is %s", self.ONLINE)
        self.first_track_on_release = ""

    @property
    def ONLINE(self):
        status = self.collection.ONLINE
        log.debug("CTRL: Collection model has ONLINE status %s", status)
        return status

    @property
    def d(self):
        discogs_cli_o = self.collection.d
        log.debug("CTRL: Getting Collection.d instance from MODEL: %s", discogs_cli_o)
        return discogs_cli_o

    @property
    def me(self):
        discogs_me_o = self.collection.d
        log.debug("CTRL: Getting Collection.me instance from MODEL: %s", discogs_me_o)
        return discogs_me_o

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
                return False
            else:
                #if len(search_results) == 1:
                #    self.cli.p('Found release: {} - {}'.format(search_results[0][3],
                #                                          search_results[0][1]))
                #    return search_results
                #else:
                self.cli.p('Found releases:')
                for cnt,release in enumerate(search_results):
                    self.cli.p('({}) {} - {}'.format(cnt, release[3], release[1]))
                #num_search_results = [[cnt,rel] for cnt,rel in enumerate(search_results)]
                #print(num_search_results)
                answ = self.cli.ask('Which release? (0) ')
                if answ == '':
                    answ = 0
                else:
                    answ = int(answ)
                return [search_results[answ]]
                #return num_search_results[answ][0]

    def print_and_return_first_d_release(self, discogs_results, _searchterm, _db_releases):
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
                    #return release_details[0]
                    log.info("Compiled Discogs release_details: {}".format(release_details))
                    return release_details
            except UnboundLocalError:
                log.error("Discogs collection was not imported to DiscoBASE. Use 'disco import' command!")
                #raise unb
                raise SystemExit(1)
        return None

    def view_all_releases(self):
        self.cli.p("Showing all releases in DiscoBASE.")
        #all_releases_result = self.cli.trim_table_fields(
        #    self.collection.get_all_db_releases())
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
                            last_row_id = self.collection.create_release(result.id,
                                    result.title, artists, d_catno, d_coll = True)
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
        #print(dir(me.collection_folders[0].releases))
        #print(dir(me))
        #print(me.collection_item)
        #if not force == True:
        self.cli.p("Asking Discogs for release ID {:d}".format(
               _release_id))
        result = self.collection.get_d_release(_release_id)
        if not result:
            raise SystemExit(3)
        else:
            self.cli.p("Release ID is valid: {}\n".format(result.title) +
                  "Let's see if it's in your collection, this might take some time...")
            in_coll = self.collection.is_in_d_coll(_release_id)
            if in_coll:
                artists = self.collection.d_artists_to_str(in_coll.release.artists)
                d_catno = self.collection.d_get_first_catno(in_coll.release.labels)
                self.cli.p(
                  "Found it in collection: {} - {} - {}.\nImporting to DiscoBASE.".format(
                  in_coll.release.id, artists, in_coll.release.title))
                self.collection.create_release(in_coll.release.id, in_coll.release.title,
                  artists, d_catno, d_coll = True)
            else:
                self.cli.error_not_the_release()
        self.cli.duration_stats(start_time, 'Discogs import') # print time stats

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
            d_artists = item.release.artists # we'll need it again with tracks
            artists = self.collection.d_artists_to_str(d_artists)
            first_catno = self.collection.d_get_first_catno(item.release.labels)
            print('Release {} - "{}" - "{}"'.format(item.release.id, artists,
                  item.release.title))
            rel_created = self.collection.create_release(item.release.id,
                  item.release.title, artists, first_catno, d_coll = True)
            # create_release will return False if unsuccessful
            if rel_created:
                self.releases_added += 1
            else:
                self.releases_db_errors += 1
                log.error(
                  'importing release "{}" Continuing anyway.'.format(
                      item.release.title))
            if tracks:
                try:
                    tracklist = item.release.tracklist
                    for track in tracklist:
                        tr_artists = self.collection.d_artists_parse(
                          tracklist, track.position, d_artists)
                        tr_title = track.title
                        if self.collection.upsert_track(item.release.id,
                              track.position, tr_title, tr_artists):
                            self.tracks_added += 1
                            msg_tr_add = 'Track "{}" - "{}"'.format(
                                  tr_artists, tr_title)
                            log.info(msg_tr_add)
                            print(msg_tr_add)
                        else:
                            self.tracks_db_errors += 1
                            log.error(
                              'importing track. Continuing anyway.')
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
            print() # leave space after a release and all its tracks
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

        self.cli.duration_stats(start_time, 'Discogs import') # print time stats

    def bpm_report(self, bpm, pitch_range):
        possible_tracks = self.collection.get_tracks_by_bpm(bpm, pitch_range)
        tr_sugg_msg = '\nShowing tracks with a BPM around {}. Pitch range is +/- {}%.'.format(bpm, pitch_range)
        self.cli.p(tr_sugg_msg)
        if possible_tracks:
            max_width = self.cli.get_max_width(possible_tracks,
              ['chosen_key', 'chosen_bpm'], 3)
            for tr in possible_tracks:
                key_bpm_and_space = self.cli.combine_fields_to_width(tr,
                  ['chosen_key', 'chosen_bpm'], max_width)
                catno = tr['d_catno'].replace(' ','')
                self.cli.p('{}{} - {} [{} ({}) {}]'.format(
                     key_bpm_and_space, tr['d_artist'], tr['d_track_name'],
                      catno, tr['d_track_no'], tr['discogs_title']))

    def key_report(self, key):
        possible_tracks = self.collection.get_tracks_by_key(key)
        tr_sugg_msg = '\nShowing tracks with key {}'.format(key)
        self.cli.p(tr_sugg_msg)
        if possible_tracks:
            max_width = self.cli.get_max_width(possible_tracks,
              ['chosen_key', 'chosen_bpm'], 3)
            for tr in possible_tracks:
                #print("in key_report: {}".format(tr['chosen_key']))
                #print("in key report: {}".format(tr['chosen_bpm']))
                key_bpm_and_space = self.cli.combine_fields_to_width(tr,
                  ['chosen_key', 'chosen_bpm'], max_width)
                self.cli.p('{}{} - {} [{} ({}) {}]:'.format(
                  key_bpm_and_space, tr['d_artist'], tr['d_track_name'],
                  tr['d_catno'], tr['d_track_no'], tr['discogs_title']))

    def key_and_bpm_report(self, key, bpm, pitch_range):
        possible_tracks = self.collection.get_tracks_by_key_and_bpm(key, bpm, pitch_range)
        tr_sugg_msg = '\nShowing tracks with key "{}" and a BPM around {}. Pitch range is +/- {}%.'.format(key, bpm, pitch_range)
        self.cli.p(tr_sugg_msg)
        if possible_tracks:
            max_width = self.cli.get_max_width(possible_tracks,
              ['chosen_key', 'chosen_bpm'], 3)
            for tr in possible_tracks:
                key_bpm_and_space = self.cli.combine_fields_to_width(tr,
                  ['chosen_key', 'chosen_bpm'], max_width)
                self.cli.p('{}{} - {} [{} ({}) {}]:'.format(
                  key_bpm_and_space, tr['d_artist'], tr['d_track_name'],
                  tr['d_catno'], tr['d_track_no'], tr['discogs_title']))

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
                print("") # space for readability
                continue # jump to next iteration, nothing more to do here

            if name or artist:
                print('Adding Track {} on "{}" ({})'.format(
                      d_track_no, discogs_title, d_release_id))
                print('{} - {}'.format(artist, name))
                if self.collection.upsert_track(d_release_id,
                      d_track_no, name, artist):
                    self.tracks_added += 1
                else:
                    self.tracks_db_errors += 1
                self.cli.brainz_processed_so_far(self.processed, self.processed_total)
                self.processed += 1
                print("") # space for readability
            else:
                print('Either track or artist name not found on "{}" ({}) - Track {} really existing?'.format(
                      discogs_title, d_release_id, d_track_no))
                self.tracks_not_found_errors += 1
                self.cli.brainz_processed_so_far(self.processed, self.processed_total)
                self.processed += 1
                print("") # space for readability

        if offset:
            processed_real = self.processed_total - offset
        else:
            processed_real = self.processed_total
        print('Processed: {}. Added Artist/Track info to DiscoBASE: {}.'.format(
            processed_real, self.tracks_added))
        print('Database errors: {}. Not found on Discogs errors: {}.'.format(
            self.tracks_db_errors, self.tracks_not_found_errors))
        print("") # space for readability

        self.cli.duration_stats(start_time, 'Updating track info') # print time stats
        return True # we did at least something and thus were successfull

    def update_single_track_or_release_from_discogs(self, rel_id, rel_title, track_no):
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
        log.debug('CTRL: update_track_from_brainz: match detail option is: {}'.format(
              detail))
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
            release_mbid, rec_mbid = None, None # we are filling these
            key, chords_key, bpm = None, None, None # searched later, in this order
            #d_release_id = track['d_release_id'] # from track table
            discogs_id = track['discogs_id'] # from release table
            d_track_no = track['d_track_no']
            user_rec_mbid = track['m_rec_id_override']

            log.info('CTRL: Trying to match Discogs release {} "{}"...'.format(
                discogs_id, track['discogs_title']))
            d_rel = self.collection.get_d_release(discogs_id) # 404 is handled here

            def _warn_skipped(m): # prints skipped-message and processed-count
                log.warning(m)
                self.cli.brainz_processed_so_far(processed, processed_total)
                print('') # space for readability

            if not d_rel:
                m = "Skipping. Cant't fetch Discogs release."
                _warn_skipped(m)
                processed += 1
                continue # jump to next track
            else:
                if not track['d_track_no']: # no track number in db -> not imported
                    # FIXME errors_not_imported
                    m = f'Skipping. No track number for '
                    m+= f'"{track["discogs_title"]}" in DiscoBASE.\n'
                    m+= f'Did you import Track details from Discogs yet? (-u)'
                    _warn_skipped(m)
                    errors_not_imported += 1
                    processed += 1
                    continue # jump to next track
                elif not track['d_track_name']: # no track name in db -> ask discogs
                    # FIXME why was get_d_release needed here? it's above already???
                    #d_rel = self.collection.get_d_release(discogs_id) # 404 is handled here
                    log.warning('No track name in DiscoBASE, asking Discogs...')
                    d_track_name = self.collection.d_tracklist_parse(
                        d_rel.tracklist, track['d_track_no'])
                    if not d_track_name: # no track name on Discogs -> give up
                        m = f'Skipping. Track number {track["d_track_no"]} '
                        m+= f'not existing on release "{track["discogs_title"]}"'
                        _warn_skipped(m)
                        errors_not_found += 1
                        processed += 1
                        continue # jump to next track
                    print(f'Track name found on Discogs: "{d_track_name}"')
                    warns_discogs_fetches += 1
                else:
                    d_track_name = track['d_track_name'] # track name in db, good

                if not track['d_catno']: # no CatNo in db -> ask discogs
                    log.warning('No catalog number in DiscoBASE, asking Discogs...')
                    d_catno = d_rel.labels[0].data['catno']
                    print(f'Catalog number found on Discogs: "{d_artist}"')
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
                #print(dir(d_rel.tracklist[1]))
                #d_rel_track_count = len(d_rel.tracklist)
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

                print("Key: {}, Chords Key: {}, BPM: {}".format(
                    key, chords_key, bpm))

                # update release table
                ok_release = self.collection.update_release_brainz(discogs_id,
                    release_mbid, bmatch.release_match_method)
                if ok_release:
                    print('Release table updated successfully.')
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
                    print('Track table updated successfully.')
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
            print('') # space for readability

        if offset:
            processed_real = processed_total - offset
        else:
            processed_real = processed_total
        self.cli.brainz_processed_report(processed_real, added_release,
          added_rec, added_key, added_chords_key, added_bpm, errors_db,
          errors_not_found, errors_no_rec_AB, errors_not_imported,
          warns_discogs_fetches)
        self.cli.duration_stats(start_time, 'Updating track info') # print time stats
        return True # we are through all tracks, in any way, this is a success

    def update_all_tracks_from_brainz(self, detail=1, offset=0):
        if not self.ONLINE:
            self.cli.p("Not online, can't pull from AcousticBrainz...")
            return False # exit method we are offline
        tracks = self.collection.get_all_tracks_for_brainz_update(
              offset=offset)
        match_ret = self.update_tracks_from_brainz(tracks, detail,
              offset=offset)
        return match_ret

    def update_single_track_or_release_from_brainz(self, rel_id, rel_title, track_no,
          detail):
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

from discodos.utils import * # some of this is a view thing right?
from discodos.models import *
from discodos.views import *
from abc import ABC, abstractmethod
from discodos import log, db # db should only be in model.py
from tabulate import tabulate as tab # should be only in views.py
import pprint as p
from datetime import time
from discodos.gui import *

# mix controller class (abstract) - common attrs and methods  for gui and cli
class Mix_ctrl_common (ABC):
    def __init__():
        pass

    @property
    def id():
        return self.mix.id

# mix controller class CLI implementation
class Mix_ctrl_cli (Mix_ctrl_common):

    def __init__(self, db_conn, mix_name_or_id, _user_int, db_file = False):
        self.mix = Mix(db_conn, mix_name_or_id, db_file) # instantiate the Mix model class
        self.cli = Mix_view_cli() # instantiatie the Mix view class (the CLI)
        self.user = _user_int # take an instance of the User_int class and set as attribute

    def create(self):
        if is_number(self.mix.name_or_id):
            log.error("Mix name can't be a number!") # log is everywhere, also in view
        else:
            print_help("Creating new mix \"{}\".".format(self.mix.name)) # view
            answers = self._create_ask_details() # view with questions from common
            created_id = self.mix.create(answers['played'], answers['venue']) # model
            self.mix.db_conn.commit() # model
            print_help("New mix created with ID {}.".format(created_id)) # view
            self.view_mixes_list() # view

    def _create_ask_details(self):
        played = ask_user("When did you (last) play it? eg 2018-01-01 ")
        venue = ask_user(text="And where? ")
        return {'played': played, 'venue': venue}

    def view_mixes_list(self):
        """
        view a list of all mixes


        @param
        @return
        @author
        """
        mixes_data = self.mix.get_all_mixes()
        self.cli.tab_mixes_list(mixes_data)

    def view(self):
        if self.mix.id_existing:
            self.cli.tab_mix_info_header(self.mix.info)
            if self.user.WANTS_VERBOSE_MIX_TRACKLIST:
                full_mix = self.mix.get_full_mix(verbose = True)
            else:
                full_mix = self.mix.get_full_mix(verbose = False)

            if not full_mix:
                print_help("No tracks in mix yet.")
            else:
                # newline chars after 24 chars magic, our new row_list:
                # FIXME this has to move to Mix_cli class or maybe also useful in Mix_gui class?
                # in any case: move to separate method
                cut_pos = 16
                full_mix_nl = []
                # first convert list of tuples to list of lists:
                for tuple_row in full_mix:
                    full_mix_nl.append(list(tuple_row))
                # now put newlines if longer than cut_pos chars
                for i, row in enumerate(full_mix_nl):
                    for j, field in enumerate(row):
                        if not is_number(field) and field is not None:
                            if len(field) > cut_pos:
                                cut_pos_space = field.find(" ", cut_pos)
                                log.debug("cut_pos_space index: %s", cut_pos_space)
                                # don't edit if no space following (almost at end)
                                if cut_pos_space == -1:
                                    edited_field = field
                                    log.debug(edited_field)
                                else:
                                    edited_field = field[0:cut_pos_space] + "\n" + field[cut_pos_space+1:]
                                    log.debug(edited_field)
                                #log.debug(field[0:cut_pos_space])
                                #log.debug(field[cut_pos_space:])
                                full_mix_nl[i][j] = edited_field

                # debug only
                for row in full_mix_nl:
                   log.debug(str(row))
                log.debug("")
                # now really
                if self.user.WANTS_VERBOSE_MIX_TRACKLIST:
                    self.cli.tab_mix_table(full_mix_nl, _verbose = True)
                else:
                    self.cli.tab_mix_table(full_mix_nl, _verbose = False)
        else:
            print_help("Mix \"{}\" is not existing yet!".format(self.mix.name_or_id))

    def delete(self):
        if self.mix.id_existing:
            if self._delete_confirm() == True:
                self.mix.delete()
                self.mix.db_conn.commit()
                print_help("Mix \"{} - {}\" deleted successfully.".format(self.mix.id, self.mix.name))
        else:
           print_help("Mix \"{}\" doesn't exist.".format(self.mix.name_or_id))

    def edit_track(self, edit_track):
        if self.mix.id_existing:
            print_help("Editing track "+edit_track+" in \""+
                        self.mix.name+"\":")
            track_details = self.mix.get_one_mix_track(edit_track)
            if track_details:
                print_help("{} - {} - {}".format(
                           track_details['discogs_title'],
                           track_details['d_track_no'],
                           track_details['d_track_name']))
                log.info("current d_release_id: %s", track_details['d_release_id'])
                edit_answers = self._edit_track_ask_details(track_details,
                        self.cli._edit_track_questions)
                for a in edit_answers.items():
                    log.info("answers: %s", str(a))
                update_ok = self.mix.update_track_in_mix(track_details, edit_answers)
                if update_ok:
                    print_help("Track edit was successful.")
                else:
                    log.error("Something went wrong on mix_track edit!")
                    raise SystemExit(1)
                self.view()
            else:
                print_help("No track "+edit_track+" in \""+
                            self.mix.name+"\".")
        else:
            print_help("Mix unknown: \"{}\".".format(self.mix.name_or_id))

    def _edit_track_ask_details(self, _track_det, edit_track_questions):
        #print(_track_det['d_track_no'])
        # collect answers from user input
        answers = {}
        answers['track_pos'] = "not a number"
        #answers['track_pos'] = ""
        for db_field, question in edit_track_questions:
            if db_field == 'track_pos':
                while not is_number(answers['track_pos']):
                    answers[db_field] = ask_user(
                                             question.format(_track_det[db_field]))
                    if answers[db_field] == "":
                        answers[db_field] = _track_det[db_field]
                        break
            else:
                answers[db_field] = ask_user(
                                         question.format(_track_det[db_field]))
                if answers[db_field] == "":
                    log.info("Answer was empty, keeping previous value: %s",
                             _track_det[db_field])
                    answers[db_field] = _track_det[db_field]
        #pprint.pprint(answers) # debug
        return answers

    def bulk_edit_tracks(self, fields_str, first_track):
        log.debug("bulk_edit_tracks args: {} {}".format(fields_str, first_track))
        fields_list = fields_str.split(',')
        log.debug('fields split: {}'.format(fields_list))
        if not first_track:
            first_track = 1
        if self.mix.id_existing:
            for track in self.mix.get_full_mix(verbose = True):
                if not track['track_pos'] < first_track:
                    self.cli.print_help(
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
                    log.debug(bulk_questions)
                    edit_answers = self._edit_track_ask_details(track_details,
                        bulk_questions)
                    update_ok = self.mix.update_mix_track_and_track_ext(track_details,
                            edit_answers)
                    print("") # just some space

    def reorder_tracks(self, startpos = 1):
        reorder_pos = int(startpos)
        reordered = self.mix.reorder_tracks(startpos)
        if not reordered:
            log.error("Reorder failed. No track {} in mix.".format(startpos))
        else:
            log.info("Reordering tracks successful")
            self.view()

    def delete_track(self, delete_track_pos):
         really_del = ask_user(text="Delete Track {} from mix {}? ".format(
                                      delete_track_pos, self.mix.id))
         if really_del.lower() == "y":
             successful = self.mix.delete_track(delete_track_pos)
             # reorder existing and print tracklist
             if successful:
                 if delete_track_pos == 1:
                    self.mix.reorder_tracks(1)
                 else:
                    self.mix.reorder_tracks(delete_track_pos - 1)
                 self.view()
             else:
                 print_help("Delete failed, maybe nonexistent track position?")

# definitely cli specific

    def _delete_confirm(self):
        really_delete = ask_user(
            "Are you sure you want to delete mix \"{} - {}\" and all its containing tracks? ".format(
                self.mix.id, self.mix.name))
        if really_delete == "y": return True
        else: return False

    def add_offline_track(self, rel_list, track_no, pos):
        if rel_list:
            self._add_track(rel_list[0][0], rel_list[0][1], track_no, pos)

    def add_discogs_track(self, rel_list, track_no, pos):
        log.info("discogs rel_list: {}".format(rel_list))
        if rel_list:
            self._add_track(rel_list[0][0], rel_list[0][2], track_no, pos)
        else:
            log.error("No release to add.")


    # _add_track should only be called from add_offline_track() and add_discogs_track()
    def _add_track(self, _release_id, _release_title, _track_no, _pos):
        if not _track_no:
            track_to_add = self.cli.ask_user_for_track()
        else:
            log.debug("_track_no was given, value is".format(_track_no))
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
            elif is_number(last_track[0]):
                # no position was given, tracks already mix
                if self.cli.really_add_track(track_to_add, _release_title,
                                             self.mix.id, last_track[0]+1):

                    current_id = self.mix.add_track(_release_id,
                                                    track_to_add, track_pos = last_track[0] + 1)
            else:
                # no position and it's the first track ever added
                if self.cli.really_add_track(track_to_add, _release_title,
                                             self.mix.id, 1):

                    current_id = self.mix.add_track(_release_id,
                                                    track_to_add, track_pos = 1)
            # FIXME untested if this is actually a proper sanity check
            log.debug("Value of current_id in add_offline_track: {}".format(current_id))
            if current_id:
                self.view()
                #return True
            else:
                log.error("Add track to DB failed!")
                #return False
        else:
            self.cli.print_help("Mix ID {} is not existing yet.".format(self.mix.id))
            return False

    def pull_track_info_from_discogs(self, coll_ctrl, start_pos = False):
        if coll_ctrl.ONLINE:
            if self.mix.id_existing:
                self.cli.print_help("Let's update current mixes tracks with info from Discogs...")
                mixed_tracks = self.mix.get_tracks_of_one_mix(start_pos)
            else:
                self.cli.print_help("Let's update ALL tracks in ALL mixes with info from Discogs...")
                mixed_tracks = self.mix.get_all_tracks_in_mixes()
            for mix_track in mixed_tracks:
                name, artist = "", ""
                coll_ctrl.collection.rate_limit_slow_downer(remaining=20, sleep=3)
                #try: # handle error 404 when release is not on discogs
                # quick and dirty: 404 is handled in this method:
                if coll_ctrl.collection.get_d_release(mix_track[2]):
                    name = coll_ctrl.cli.d_tracklist_parse(
                            coll_ctrl.d.release(mix_track[2]).tracklist, mix_track[3])
                    artist = coll_ctrl.collection.d_artists_parse(
                               coll_ctrl.d.release(mix_track[2]).tracklist,
                               mix_track[3],
                               coll_ctrl.d.release(mix_track[2]).artists)
                else:
                    print("") # space for readability

                if name:
                    print("Adding track info: {} {} - {} - {}".format(
                        mix_track[2], mix_track[3], artist, name))
                    coll_ctrl.collection.create_track(mix_track[2], mix_track[3], name, artist)
                else:
                    #print("Adding track info: "+ str(mix_track[2])+" "+
                    #        mix_track[3])
                    print("Adding track info: {} {}".format(
                        mix_track[2], mix_track[3]))
                    log.error("No trackname found for Tr.Pos %s",
                            mix_track[3])
                    log.error("Probably you misspelled? (eg A vs. A1)\n")
        else:
            self.cli.print_help("Not online, can't pull from Discogs...")

    def copy_mix(self):
        self.cli.print_help("Copying mix {} - {}.".format(self.mix.id, self.mix.name))
        copy_tr = self.mix.get_tracks_to_copy()
        new_mix_name = self.cli.ask_user("How should the copy be named? ")
        new_mix_id = self.mix.create(self.mix.played, self.mix.venue, new_mix_name)
        new_mix = Mix(self.mix.db_conn, new_mix_id)
        for tr in copy_tr:
            log.debug("CTRL copy_mix: This is tr: {}, {}, {}, {}, {}, ".format(
                tr[0], tr[1], tr[2], tr[3], tr[4]))
            new_mix.add_track(tr[0], tr[1], tr[2], tr[3], tr[4])
            #release, track_no, track_pos, trans_rating='', trans_notes=''
        new_mix.db_conn.commit()
        self.cli.print_help("Copy mix successful. New ID is {}.".format(new_mix.id))

    def update_in_d_coll(self, coll_ctrl, start_pos = False):
        if coll_ctrl.ONLINE:
            if self.mix.id_existing:
                self.cli.print_help("Let's update Discogs collection field in current mixes releases...")
                db_releases = self.mix.get_releases_of_one_mix(start_pos)
                for db_rel in db_releases:
                    pass
            #else:
            #    self.cli.print_help("Let's update ALL tracks in ALL mixes with info from Discogs...")
            #    mixed_tracks = self.mix.get_all_tracks_in_mixes()

# Collection controller common methods
class Coll_ctrl_common (ABC):

    def __init__():
        pass

# Collection controller class
class Coll_ctrl_cli (Coll_ctrl_common):
    """
    manages the record collection, offline and with help of discogs data

    @param
    @return
    @author
    """

    def __init__(self, _db_conn, _user_int, _userToken, _appIdentifier):
        self.user = _user_int # take an instance of the User_int class and set as attribute
        self.db_conn = _db_conn
        self.user = _user_int
        self.collection = Collection(self.db_conn)
        self.cli = Collection_view_cli() # instantiate cli frontend class 
        if self.user.WANTS_ONLINE:
            if not self.collection.discogs_connect(_userToken, _appIdentifier):
                log.error("connecting to Discogs API, let's stay offline!\n")
        # just set this for compatibilty reasons, currently used in cli.py, will prob. removed
        #self.ONLINE = self.collection.ONLINE
        log.info("CTRL: Initial ONLINE status is %s", self.ONLINE)

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

    def search_release(self, _searchterm): # online or offline search is decided in this method
        if self.collection.ONLINE:
            if is_number(_searchterm):
                print_help('Searchterm is a number, trying to add Release ID to collection...')
                self.add_release(int(_searchterm))

            db_releases = self.collection.get_all_db_releases()
            print_help('Searching Discogs for Release ID or Title: {}'.format(_searchterm))
            search_results = self.collection.search_release_online(_searchterm)

            # SEARCH RESULTS OUTPUT HAPPENS HERE
            compiled_results_list = self.cli.print_found_discogs_release(
                                        search_results, _searchterm, db_releases)
            return compiled_results_list
            #if compiled_results_list:
            #    if len(compiled_results_list) == 1:
            #        print_help('Found release: {}'.format(compiled_results_list[0][1]))
            #        return compiled_results_list
            #    else:
            #        print_help('Found several releases:')
            #        for cnt,release in enumerate(compiled_results_list):
            #            print_help('{} - {}'.format(cnt, release[1]))
            #        answ = int(self.cli.ask_user('Which release? '))
            #        return [compiled_results_list[answ]]

        else:
            print_help('Searching database for ID or Title: {}'.format(_searchterm))
            search_results = self.collection.search_release_offline(_searchterm)
            if search_results:
                if len(search_results) == 1:
                    print_help('Found release: {} - {}'.format(search_results[0][3],
                                                          search_results[0][1]))
                    return search_results
                else:
                    print_help('Found several releases:')
                    for cnt,release in enumerate(search_results):
                        print_help('({}) {} - {}'.format(cnt, release[3], release[1]))
                        #for col in release:
                        #    print(col)
                    #num_search_results = [[cnt,rel] for cnt,rel in enumerate(search_results)]
                    #print(num_search_results)
                    answ = self.cli.ask_user('Which release? (0) ')
                    if answ == '':
                        answ = 0
                    else:
                        answ = int(answ)
                    return [search_results[answ]]
                    #return num_search_results[answ][0]
            else:
                print_help('Nothing found.')
                return False

    def view_all_releases(self):
        self.cli.print_help("Showing all releases in DiscoBASE.")
        all_releases_result = self.collection.get_all_releases()
        self.cli.tab_all_releases(all_releases_result)

    def track_report(self, track_searchterm):
        release = self.search_release(track_searchterm)
        if release:
            track_no = self.cli.ask_user_for_track()
            if self.collection.ONLINE == True:
                rel_id = release[0][0]
                rel_name = release[0][3]
            else:
                rel_id = release[0][0]
                rel_name = release[0][1]
            track_occurences = self.collection.track_report_occurences(rel_id, track_no)
            self.cli.print_help('\nTrack-combination-report for track {} on "{}":'.format(
                track_no, rel_name))
            if track_occurences:
                for tr in track_occurences:
                    self.cli.print_help("Snippet from Mix {} - {}:".format(
                        tr['mix_id'], tr['name']))
                    report_snippet = self.collection.track_report_snippet(tr['track_pos'], tr['mix_id'])
                    self.cli.tab_mix_table(report_snippet, _verbose = True)
        else:
            raise SystemExit(3)

    # ADD RELEASE TO COLLECTION
    def add_release(self, release_id):
        self.cli.exit_if_offline(self.collection.ONLINE)
        #if args.add_release_id:
        if is_number(release_id):
            # setup.py argparser only allows integer, this is for calls from somewhere else
            #if db.search_release_id(conn, args.add_release_id):
            if self.collection.search_release_id(release_id):
                self.cli.print_help(
                  "Release ID is already existing in DiscoBASE, won't add it to your Discogs collection."
                   )
            else:
                self.cli.print_help("Asking Discogs if release ID {:d} is valid.".format(
                       release_id))
                result = self.collection.d.release(release_id)
                artists = self.collection.d_artists_to_str(result.artists)
                if result:
                    log.debug(dir(result))
                    self.cli.print_help("Adding \"{}\" to collection".format(result.title))
                    for folder in self.collection.me.collection_folders:
                        if folder.id == 1:
                            folder.add_release(release_id)
                            #import_release(conn, d, me, args.add_release_id)
                            #last_row_id = db.create_release(conn, result, collection_item = False)
                            last_row_id = self.collection.create_release(result.id,
                                    result.title, artists, d_coll = True)
                    if not last_row_id:
                        #self.cli.print_help("This is not the release you are looking for!")
                        self.cli.error_not_the_release()

    # import specific release ID into DB
    def import_release(self, _release_id):
        self.cli.exit_if_offline(self.collection.ONLINE)
        #print(dir(me.collection_folders[0].releases))
        #print(dir(me))
        #print(me.collection_item)
        #if not force == True:
        self.cli.print_help("Asking Discogs for release ID {:d}".format(
               _release_id))
        result = self.collection.get_d_release(_release_id)
        if not result:
            raise SystemExit(3)
        else:
            self.cli.print_help("Release ID is valid: {}\n".format(result.title) +
                  "Let's see if it's in your collection, this might take some time...")
            in_coll = self.collection.is_in_d_coll(_release_id)
            if in_coll:
                artists = self.collection.d_artists_to_str(in_coll.release.artists)
                self.cli.print_help(
                    "Found it in collection: {} - {} - {}.\nImporting to DiscoBASE.".format(
                    in_coll.release.id, artists, in_coll.release.title))
                self.collection.create_release(in_coll.release.id, in_coll.release.title,
                  self.collection.d_artists_to_str(in_coll.release.artists), d_coll = True)
            else:
                self.cli.error_not_the_release()

    def import_collection(self):
        self.cli.exit_if_offline(self.collection.ONLINE)
        self.cli.print_help(
        "Gathering your Discogs collection and importing necessary fields into DiscoBASE")
        insert_count = 0
        for r in self.collection.me.collection_folders[0].releases:
            self.collection.rate_limit_slow_downer(remaining=20, sleep=3)
            artists = self.collection.d_artists_to_str(r.release.artists)
            print("Release :", r.release.id, "-", artists, "-",  r.release.title)
            rowcount = self.collection.create_release(r.release.id, r.release.title,
                    artists, d_coll = True)
            # create_release will return False if unsuccessful
            if rowcount:
                insert_count = insert_count + 1
                print("Created so far:", insert_count, "")
                log.info("discogs-rate-limit-remaining: %s",
                         self.collection.d._fetcher.rate_limit_remaining)
                print()
            else:
                log.error("Something wrong while importing \"{}\"\n".format(r.release.title))


class Mix_ctrl_gui(Mix_ctrl_common):

    
    def view_mixes_list(self):
        """
        view a list of all mixes


        @param
        @return
        @author
        """
        mixes_data = self.mix.get_all_mixes()
        return mixes_data
        


    

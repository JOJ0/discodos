from discodos.utils import * # some of this is a view thing right?
from discodos.models import *
from discodos.views import *
from abc import ABC, abstractmethod
from discodos import log, db # db should only be in model.py
from tabulate import tabulate as tab # should be only in views.py
import pprint

# mix controller class (abstract) - common attrs and methods  for gui and cli
class Mix_ctrl_common (ABC):

    def _add_track_to_db_wrapper(self, release_id, track_no, pos = False):
        """
         like in first version add_track_to_mix(conn, _mix_id, _track, _rel_list,
         _pos=None),
         also add_track_at_pos() schould be handled here.

        @param int release_id : simply the release_id, all figuring out stuff has been done before in add_track_discogs() or add_track_db()
        @param string track_no : eg A1, A2 as a string
        @return  :
        @author
        """
        pass

# mix controller class CLI implementation
class Mix_ctrl_cli (Mix_ctrl_common):

    def __init__(self, db_conn, mix_name_or_id, _user_int):
        self.mix = Mix(db_conn, mix_name_or_id) # instantiate the Mix model class
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
                full_mix = self.mix.get_full_mix("fine")
            else:
                full_mix = self.mix.get_full_mix("coarse")

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
                edit_answers = self._edit_track_ask_details(track_details)
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

    def _edit_track_ask_details(self, _track_det):
        #print(_track_det['d_track_no'])
        # collect answers from user input
        answers = {}
        answers['track_pos'] = "x"
        for db_field, question in self.cli._edit_track_questions:
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

    # add database track wrapper
    def add_offline_track(self, rel_list, track_no, pos):
        self._add_track(rel_list[0][0], rel_list[0][1], track_no, pos)

    # add discogs track wrapper
    def add_discogs_track(self, rel_list, track_no, pos):
        log.info("discogs rel_list: {}".format(rel_list))
        self._add_track(rel_list[0][0], rel_list[0][2], track_no, pos)

    # _add_track should only be called from add_offline_track() and add_discogs_track()
    def _add_track(self, _release_id, _release_title, _track_no, _pos):
        if not _track_no:
            track_to_add = self.cli.ask_user("Which track? ")
        else:
            log.info("_track_no was given, value is".format(_track_no))
            track_to_add = _track_no
        if _pos == None:
            log.info("_pos was None, setting to 0")
            _pos = 0
        log.info("This is _pos: {}".format(_pos))
        log.info("This is track_to_add: {}".format(track_to_add))
        log.info("This is _release_id: %s", _release_id)
        log.info("This is _release_title: %s", _release_title)
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
                if self.cli.really_add_track(track_to_add, _release_name,
                                             self.mix.id, 1):

                    current_id = self.mix.add_track(_release_id,
                                                    track_to_add, track_pos = 1)
            # FIXME untested if this is actually a proper sanity check
            log.info("Value of current_id in add_offline_track: {}".format(current_id))
            if current_id:
                self.view()
                #return True
            else:
                log.error("Add track to DB failed!")
                #return False
        else:
            self.cli.print_help("Mix ID {} is not existing yet.".format(self.mix.id))
            return False


# Collection controller class
class Coll_ctrl_cli (object):
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
        self.collection = Collection(_db_conn)
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

    def search_release(self, _searchterm): # online on offline search is decided in this method
        if self.collection.ONLINE:
            db_releases = self.collection.get_all_db_releases()
            print_help('Searching Discogs for Release ID or Title: {}'.format(_searchterm))
            search_results = self.collection.search_release_online(_searchterm)

            # SEARCH RESULTS OUTPUT HAPPENS HERE
            compiled_results_list = self.cli.print_found_discogs_release(
                                        search_results, _searchterm, db_releases)
            return compiled_results_list
        else:
            print_help('Searching database for ID or Title: {}'.format(_searchterm))
            search_results = self.collection.search_release_offline(_searchterm)
            return search_results

    def view_all_releases(self):
        self.cli.print_help("Showing all releases in DB.")
        all_releases_result = self.collection.get_all_releases()
        self.cli.tab_all_releases(all_releases_result)

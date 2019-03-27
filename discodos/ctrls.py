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

    def _reorder_tracks_db_wrapper(self, startpos = 1):
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
                            self.name+"\".")
        else:
            print_help("Mix unknown: \"{}\".".format(self.mix.mix_name_or_id))


# definitely cli specific

    def _delete_confirm(self):
        really_delete = ask_user(
            "Are you sure you want to delete mix \"{} - {}\" and all its containing tracks? ".format(
                self.mix.id, self.mix.name))
        if really_delete == "y": return True
        else: return False

    def _del_track_confirm(self, pos):
        pass

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

        # tabulate tracklist in DETAIL
        def _mix_table_fine(_mix_data):
            return tab(_mix_data, tablefmt="pipe",
                headers=["#", "Release", "Track\nName", "Track\nPos", "Key", "BPM",
                         "Key\nNotes", "Trans.\nRating", "Trans.\nR. Notes", "Track\nNotes"])

        # tabulate header of mix-tracklist
        def _mix_info_header(_mix_info):
            return tab([_mix_info], tablefmt="plain",
                headers=["Mix", "Name", "Created", "Updated", "Played", "Venue"])

        print_help(_mix_info_header(self.info))
        if _verbose:
            print_help(_mix_table_fine(_mix_data))
        else:
            print_help(_mix_table_coarse(_mix_data))



    def add_track_from_db(self, release, track_no, pos = False):
        """
        release_dict_db and release_dict_discogs look a little different


        @param int pos : track position in mix
        @param release_dict_db release : a release_dict object returned from offline db: eg: found_in_db_releases[123456]
        @param string track_no : eg. A1, A2 
        @return  :
        @author
        """
        pass

    def add_track_from_discogs(self, release, track_no, pos = False):
        """
         release_dict_db and release_dict_discogs look a little different


        @param int pos : eg. 5 or 12
        @param release_dict_discogs release : eg. a releases_list + release_id index
e.g. found_releases[47114711]
        @param string track_no : e.g. A2 or A
        @return  :
        @author
        """
        pass

    def del_track(self, pos):
        pass

    def reorder_tracks(self, startpos = 1):
        pass


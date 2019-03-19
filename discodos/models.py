from discodos.utils import * # most of this should only be in view
from abc import ABC, abstractmethod
from discodos import log, db
from tabulate import tabulate as tab # should only be in view
import pprint

# mix model class
class Mix (object):

    def __init__(self, db_conn, mix_name_or_id):
        self.db_conn = db_conn
        # list of edit_track_questions is defined here once (for all child classes):
        # dbfield, question
        self._edit_track_questions = [
            ["key", "Key ({}): "],
            ["bpm", "BPM ({}): "],
            ["d_track_no", "Track # on record ({}): "],
            ["track_pos", "Move track's position ({}): "],
            ["key_notes", "Key notes/bassline/etc. ({}): "],
            ["trans_rating", "Transition rating ({}): "],
            ["trans_notes", "Transition notes ({}): "],
            ["d_release_id", "Release ID ({}): "],
            ["notes", "Other track notes: ({}): "]
        ]
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
                    except:
                        log.info("Can't get mix info.")
                        #raise Exception # use this for debugging
                except:
                    log.info("Can't get mix-name from id. Mix not existing yet?")
                    #raise Exception # use this for debugging
                    #raise SystemExit(1)

    def delete(self):
        if self.id_existing:
            if self._delete_confirm() == True:
                db.delete_mix(self.db_conn, self.id)
                self.db_conn.commit()
                print_help("Mix \"{} - {}\" deleted successfully.".format(self.id, self.name))
        else:
           print_help("Mix \"{}\" doesn't exist.".format(self.name_or_id))

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

    def edit_track(self, edit_track):
        if self.id_existing:
            print_help("Editing track "+edit_track+" in \""+
                        self.name+"\":")
            track_details = db.get_one_mix_track(self.db_conn, self.id, edit_track)
            print_help("{} - {} - {}".format(
                       track_details['discogs_title'],
                       track_details['d_track_no'],
                       track_details['d_track_name']))
            if track_details:
                log.info("current d_release_id: %s", track_details['d_release_id'])
                edit_answers = self._edit_track_ask_details(track_details)
                for a in edit_answers.items():
                    log.info("answers: %s", str(a))
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
                except Exception as edit_err:
                    log.error("Something went wrong on mix_track edit!")
                    raise edit_err
                    raise SystemExit(1)
                pretty_print_mix_tracklist(self.id, mix_info)
            else:
                print_help("No track "+edit_track+" in \""+
                            self.name+"\".")
        else:
            print_help("Mix unknown: \"{}\".".format(self.mix_name_or_id))

    def reorder_tracks(self, startpos = 1):
        pass

    def get_full_mix(self, verbosity = "coarse"):
        return db.get_full_mix(self.db_conn, self.id, verbosity)

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

    #@abstractmethod
    def _del_track_confirm(self, pos):
        pass

    #@abstractmethod
    def _create_ask_details(self):
        pass

    #@abstractmethod
    def _edit_track_ask_details(self):
        pass

    def reorder_tracks(self, startpos = 1):
        pass

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

    #@abstractmethod
    def _del_track_confirm(self, pos):
        pass

    #@abstractmethod
    def _create_ask_details(self):
        pass

    #@abstractmethod
    def _edit_track_ask_details(self):
        pass

    #@abstractmethod
    def _view_pretty(self):
        pass

# mix_cli child of mix class - cli specific stuff is handled here
class Mix_cli (Mix):

    def _delete_confirm(self):
        really_delete = ask_user(
            "Are you sure you want to delete mix \"{} - {}\" and all its containing tracks? ".format(
                self.id, self.name))
        if really_delete == "y": return True
        else: return False

    def _del_track_confirm(self, pos):
        pass

    def _edit_track_ask_details(self, _track_det):
        #print(_track_det['d_track_no'])
        # collect answers from user input
        answers = {}
        answers['track_pos'] = "x"
        for db_field, question in self._edit_track_questions:
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

    def _view_pretty(self, _mix_data, _verbose = False):
        # FIXME _mix_data should be object attribute "tracklist"
        # tabulate tracklist COARSLY
        def _mix_table_coarse(_mix_data):
            return tab(_mix_data, tablefmt="pipe",
                headers=["#", "Release", "Tr\nPos", "Trns\nRat", "Key", "BPM"])

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



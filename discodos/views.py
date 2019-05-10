from discodos.utils import * # some of this is a view thing right?
from abc import ABC, abstractmethod
from discodos import log
from tabulate import tabulate as tab # should be only in views.py
import pprint

# user interaction class - holds info about what user wants to do
# currently this only analyzes argparser args and puts it to nicely human readable properties
class User_int(object):

    def __init__(self, _args):
        self.args = _args
        self.WANTS_ONLINE = True
        self.WANTS_TO_LIST_ALL_RELEASES = False
        self.WANTS_TO_SEARCH_FOR_RELEASE = False
        self.WANTS_TO_ADD_TO_MIX = False
        self.WANTS_TO_SHOW_MIX_OVERVIEW = False
        self.WANTS_TO_SHOW_MIX_TRACKLIST = False
        self.WANTS_TO_CREATE_MIX = False
        self.WANTS_TO_EDIT_MIX_TRACK = False
        self.WANTS_TO_PULL_TRACK_INFO = False
        self.WANTS_VERBOSE_MIX_TRACKLIST = False
        self.WANTS_TO_REORDER_MIX_TRACKLIST = False
        self.WANTS_TO_ADD_AT_POSITION = False
        self.WANTS_TO_DELETE_MIX_TRACK = False
        self.WANTS_TO_ADD_RELEASE_IN_MIX_MODE = False
        self.WANTS_TO_ADD_AT_POS_IN_MIX_MODE = False
        self.WANTS_TO_COPY_MIX = False
        self.WANTS_TO_TRACK_SEARCH = False
        self.WANTS_TO_DELETE_MIX = False
        self.WANTS_TRACK_REPORT = False

        # RELEASE MODE:
        if hasattr(self.args, 'release_search'):
            if "all" in self.args.release_search:
                self.WANTS_TO_LIST_ALL_RELEASES = True
                self.WANTS_ONLINE = False
            else:
                self.WANTS_TO_SEARCH_FOR_RELEASE = True
                if (self.args.add_to_mix != 0 and self.args.track_to_add != 0
                  and self.args.add_at_pos):
                    self.WANTS_TO_ADD_AT_POSITION = True
                    #self.WANTS_TO_SHOW_MIX_TRACKLIST = True
                elif self.args.add_to_mix !=0 and self.args.track_to_add !=0:
                    self.WANTS_TO_ADD_TO_MIX = True
                else:
                    log.error("args.add_to_mix, args.track_to_add or args.add_at_pos is 0")
                    raise SystemExit(1)

        # MIX MODE
        if hasattr(self.args, 'mix_name'):
            if self.args.mix_name == "all":
                self.WANTS_TO_SHOW_MIX_OVERVIEW = True
                self.WANTS_ONLINE = False
                if self.args.create_mix == True:
                    log.error("Please provide a mix name to be created!")
                    log.error("(Mix name \"all\" is not valid.)")
                    raise SystemExit(1)
                elif self.args.delete_mix == True:
                    log.error("Please provide a mix name or ID to be deleted!")
                    raise SystemExit(1)
                if self.args.discogs_update:
                    self.WANTS_TO_PULL_TRACK_INFO = True
                    self.WANTS_ONLINE = True
            else:
                self.WANTS_TO_SHOW_MIX_TRACKLIST = True
                self.WANTS_ONLINE = False
                #if hasattr(self.args, 'create_mix')
                if self.args.create_mix:
                    self.WANTS_TO_CREATE_MIX = True
                    self.WANTS_ONLINE = False
                if self.args.edit_mix_track:
                    self.WANTS_TO_EDIT_MIX_TRACK = True
                    self.WANTS_ONLINE = False
                if self.args.verbose_tracklist:
                    self.WANTS_VERBOSE_MIX_TRACKLIST = True
                    self.WANTS_ONLINE = False
                if self.args.reorder_from_pos:
                    self.WANTS_TO_REORDER_MIX_TRACKLIST = True
                    self.WANTS_ONLINE = False
                if self.args.delete_track_pos:
                    self.WANTS_TO_DELETE_MIX_TRACK = True
                    self.WANTS_ONLINE = False
                if self.args.add_release_to_mix:
                    self.WANTS_TO_ADD_RELEASE_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    if self.args.mix_mode_add_at_pos:
                        self.WANTS_TO_ADD_AT_POS_IN_MIX_MODE = True
                if self.args.copy_mix:
                    self.WANTS_TO_COPY_MIX = True
                    self.WANTS_ONLINE = False
                if self.args.discogs_update:
                    self.WANTS_TO_PULL_TRACK_INFO = True
                    self.WANTS_ONLINE = True
                if self.args.delete_mix:
                    self.WANTS_TO_DELETE_MIX = True
                    self.WANTS_ONLINE = False

        # TRACK MODE
        if hasattr(self.args, 'track_search'):
            self.WANTS_TO_TRACK_SEARCH = True
            if self.args.track_pull:
                self.WANTS_TO_PULL_TRACK_INFO = True
            else:
                self.WANTS_TRACK_REPORT = True
                log.debug("Entered Track-combination report.")
                #log.error("track search not implemented yet.")
                #raise SystemExit(1)

        if self.args.offline_mode == True:
            self.WANTS_ONLINE = False
### End User_int class ##########################################

class Cli_view_common(ABC):
    # cli util: print a UI message
    def print_help(self, message):
        print(''+str(message)+'\n')

    # util: ask user for some string
    def ask_user(self, text=""):
        return input(text)

    def ask_user_for_track(self):
        track_no = self.ask_user("Which track? (A1) ")
        # FIXME a sanity checker, at least for online search, would be nice here.
        # also the default value is not checked, eg it could be A in reality!
        if track_no == '':
            track_no = 'A1'
        return track_no

    def tab_mix_table(self, _mix_data, _verbose = False):
        if _verbose:
            self.print_help(tab(_mix_data, tablefmt="pipe",
                headers=["#", "Release", "Track\nName", "Track\nPos", "Key", "BPM",
                         "Key\nNotes", "Trans.\nRating", "Trans.\nR. Notes", "Track\nNotes"]))
        else:
            self.print_help(tab(_mix_data, tablefmt="pipe",
                headers=["#", "Release", "Tr\nPos", "Trns\nRat", "Key", "BPM"]))


# general stuff, useful for all UIs:
class Mix_view_common(ABC):
    def __init__(self):
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

# viewing mixes in CLI mode:
class Mix_view_cli(Mix_view_common, Cli_view_common):
    def __init__(self):
        super(Mix_view_cli, self).__init__()

    def tab_mixes_list(self, mixes_data):
        tabulated = tab(mixes_data, tablefmt="simple",
                headers=["Mix #", "Name", "Created", "Updated", "Played", "Venue"])
        self.print_help(tabulated)

    def tab_mix_info_header(self, mix_info):
        self.print_help(tab([mix_info], tablefmt="plain",
                headers=["Mix", "Name", "Created", "Updated", "Played", "Venue"]))

    def really_add_track(self, track_to_add, release_name, mix_id, pos):
        quest=(
        #'Add "{:s}" on "{:s}" to mix #{:d}, at position {:d}? (y) '
        'Add "{}" on "{:s}" to mix #{}, at position {}? (y) '
            .format(track_to_add, release_name, int(mix_id), pos))
        _answ = self.ask_user(quest)
        if _answ.lower() == "y" or _answ.lower() == "":
            return True

# collection view - common things for cli and gui
class Collection_view_common(ABC):
    def __init__(self):
        #super(Collection_view_cli, self).__init__()
        pass

    def d_tracklist_parse(self, d_tracklist, track_number):
        '''gets Track name from discogs tracklist object via track_number, eg. A1'''
        for tr in d_tracklist:
            if tr.position == track_number:
                return tr.title


# viewing collection (search) outputs in CLI mode:
class Collection_view_cli(Collection_view_common, Cli_view_common):
    def __init__(self):
        super(Collection_view_cli, self).__init__()

    # Discogs: formatted output of release search results
    def print_found_discogs_release(self, discogs_results, _searchterm, _db_releases):
        # only show pages count if it's a Release Title Search
        if not is_number(_searchterm):
            self.print_help("Found "+str(discogs_results.pages )+" page(s) of results!")
        else:
            self.print_help("ID: "+discogs_results[0].id+", Title: "+discogs_results[0].title+"")
        for result_item in discogs_results:
            self.print_help("Checking " + str(result_item.id))
            for dbr in _db_releases:
                if result_item.id == dbr[0]:
                    self.print_help("Good, first matching record in your collection is:")
                    result_list=[]
                    result_list.append([])
                    result_list[0].append(result_item.id)
                    result_list[0].append(str(result_item.artists[0].name))
                    result_list[0].append(result_item.title)
                    result_list[0].append(str(result_item.labels[0].name))
                    result_list[0].append(result_item.country)
                    result_list[0].append(str(result_item.year))
                    #result_list[0].append(str(result_item.formats[0]['descriptions'][0])+
                    #           ", "+str(result_item.formats[0]['descriptions'][1]))
                    result_list[0].append(str(result_item.formats[0]['descriptions'][0])+
                               ", "+str(result_item.formats[0]['descriptions'][0]))

                    self.tab_online_search_results(result_list)
                    self.online_search_results_tracklist(result_item.tracklist)
                    break
            if result_item.id == dbr[0]:
                #return result_list[0]
                log.info("Compiled Discogs result_list: {}".format(result_list))
                return result_list
                break

    def tab_online_search_results(self, _result_list):
        self.print_help(tab(_result_list, tablefmt="simple",
                  headers=["ID", "Artist", "Release", "Label", "C", "Year", "Format"]))

    def online_search_results_tracklist(self, _tracklist):
        for track in _tracklist:
            print(track.position + "\t" + track.title)
        print()

    def tab_all_releases(self, releases_data):
        self.print_help(tab(releases_data, tablefmt="plain",
            headers=["ID", "Release name", "Last import"]))

    def error_not_the_release(self):
        log.error("This is not the release you are looking for!")
        print(r'''
                                     .=.
                                    '==c|
                                    [)-+|
                                    //'_|
                               snd /]==;\
              ''')

    def exit_if_offline(self, online):
        if not online:
            log.error("Need to be ONLINE to do that!")
            raise SystemExit(3)



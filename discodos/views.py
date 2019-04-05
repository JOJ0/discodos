from discodos.utils import * # some of this is a view thing right?
from abc import ABC, abstractmethod
from discodos import log
from tabulate import tabulate as tab # should be only in views.py
import pprint

class Cli_view_common(ABC):
    # cli util: print a UI message
    def print_help(self, message):
        print(''+str(message)+'\n')

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

    def tab_mix_table(self, _mix_data, _verbose = False):
        if _verbose:
            self.print_help(tab(_mix_data, tablefmt="pipe",
                headers=["#", "Release", "Track\nName", "Track\nPos", "Key", "BPM",
                         "Key\nNotes", "Trans.\nRating", "Trans.\nR. Notes", "Track\nNotes"]))
        else:
            self.print_help(tab(_mix_data, tablefmt="pipe",
                headers=["#", "Release", "Tr\nPos", "Trns\nRat", "Key", "BPM"]))

    def tab_mix_info_header(self, mix_info):
        self.print_help(tab([mix_info], tablefmt="plain",
                headers=["Mix", "Name", "Created", "Updated", "Played", "Venue"]))

    # util: ask user for some string
    def ask_user(self, text=""):
        return input(text)

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


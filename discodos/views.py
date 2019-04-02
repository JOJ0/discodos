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
        print_help(tabulated)

    def tab_mix_table(self, _mix_data, _verbose = False):
        if _verbose:
            print_help(tab(_mix_data, tablefmt="pipe",
                headers=["#", "Release", "Track\nName", "Track\nPos", "Key", "BPM",
                         "Key\nNotes", "Trans.\nRating", "Trans.\nR. Notes", "Track\nNotes"]))
        else:
            print_help(tab(_mix_data, tablefmt="pipe",
                headers=["#", "Release", "Tr\nPos", "Trns\nRat", "Key", "BPM"]))

    def tab_mix_info_header(self, mix_info):
        print_help(tab([mix_info], tablefmt="plain",
        #print_help(tab(mix_info, tablefmt="plain",
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


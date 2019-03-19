from discodos.utils import * # some of this is a view thing right?
from abc import ABC, abstractmethod
from discodos import log
from tabulate import tabulate as tab # should be only in views.py
import pprint

# general stuff:

# viewing mixes:
class Mix_view_cli(object):
    #def __init__():

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
                headers=["Mix", "Name", "Created", "Updated", "Played", "Venue"]))


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

from discodos.utils import * # some of this is a view thing right?
from abc import ABC, abstractmethod
from discodos import log
from tabulate import tabulate as tab # should be only in views.py
import pprint
from datetime import datetime
from datetime import date

import discodos.views as views
import discodos.ctrls as ctrls
import discodos.models as models
import discodos.utils as utils
import discodos.log as log

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from tabulate import tabulate as tab
from PIL import Image, ImageTk


# common view utils, usable in CLI and GUI
class View_common(ABC):
    def shorten_timestamp(self, sqlite_date, text = False):
        ''' remove time from timestamps we get out of the db, just leave date'''
        date_only = datetime.fromisoformat(sqlite_date).date()
        if text == True:
            return str(date_only)
        return date_only

    def format_date_month(self, sqlite_date, text = False):
        ''' format a date string to eg "May 2020" '''
        try:
            date_year_month = date.fromisoformat(
                self.none_replace(sqlite_date)).strftime("%b %Y")
        except ValueError:
            date_year_month = "-"

        if text == True:
            return str(date_year_month)
        return date_year_month

    def get_max_width(self, rows_list, keys_list, extra_space):
        '''gets max width of sqlite list of rows for given fields (keys_list)
           and add some space. FIXME: Only supports exactly 2 keys.'''
        max_width = 0
        for row in rows_list:
            row_mutable = dict(row)
            width = 0
            if row_mutable[keys_list[0]] is None:
                row_mutable[keys_list[0]] = "-"
            if row_mutable[keys_list[1]] is None:
                row_mutable[keys_list[1]] = "-"
            width = (len(row_mutable[keys_list[0]]) + len('/')
                + len(str(row_mutable[keys_list[1]])))
            #log.debug("This rows width: {}.".format(width))
            if max_width < width:
                max_width = width
        log.debug("Found a max width of {}, adding extra_space of {}.".format(
              max_width, extra_space))
        return max_width + extra_space

    def combine_fields_to_width(self, row, keys_list, set_width):
        '''takes sqlite row and keys_list, combines and fills with
           spaces up to set_width. FIXME: Only supports exactly 2 keys.'''
        row_mut = dict(row) # make sqlite row tuple mutable
        if row_mut[keys_list[0]] is None:
            row_mut[keys_list[0]] = "-"
        if row_mut[keys_list[1]] is None:
            row_mut[keys_list[1]] = "-"
        combined_key_bpm = "{}/{}".format(row_mut[keys_list[0]],
              str(row_mut[keys_list[1]]))
        combined_with_space = combined_key_bpm.ljust(set_width)
        #log.warning("Combined string: {}".format(combined_str))
        return combined_with_space

    def none_replace(self, value_to_check):
        '''replaces string "None" by empty string
           (eg. we use this to pretty empty db-fields in tkinter gui)
           empty list will be replaced by zero, so tkinter can measure something
           spaces (" ") will be replaced by empty string as well
        '''

        if value_to_check == "None":
            value_to_check = ""

        elif value_to_check == " ":
            value_to_check = ""

        elif value_to_check == []:
            value_to_check = [X]

        if value_to_check == None:
            value_to_check = ""

        return value_to_check

    def trim_table_fields(self, tuple_table):
        """this method puts \n after a configured amount of characters
        into _all_ fields of a sqlite row objects tuple list"""
        cut_pos = 16
        log.info('VIEW: Trimming table field width to max {} chars'.format(cut_pos))
        # first convert list of tuples to list of lists:
        table_nl = [dict(row) for row in tuple_table]
        # now put newlines if longer than cut_pos chars
        for i, row in enumerate(table_nl):
            for key, field in row.items():
                cut_pos_space = False # reset cut_pos_space on each field cycle
                if not is_number(field) and field is not None:
                    if len(field) > cut_pos:
                        cut_pos_space = field.find(" ", cut_pos)
                        log.debug("cut_pos_space index (next space after cut_pos): %s", cut_pos_space)
                        # don't edit if no space following (almost at end)
                        if cut_pos_space == -1:
                            edited_field = field
                        else:
                            edited_field = field[0:cut_pos_space] + "\n" + field[cut_pos_space+1:]
                        log.debug("string from 0 to cut_pos_space: {}".format(field[0:cut_pos_space]))
                        log.debug("string from cut_pos_space to end: {}".format(field[cut_pos_space:]))
                        log.debug("the final string:")
                        log.debug("{}".format(edited_field))
                        log.debug("")
                        table_nl[i][key] = edited_field
        log.debug("table_nl has {} lines".format(len(table_nl)))
        return table_nl

    def replace_key_bpm(self, list_of_rows):
        '''show key,bpm from accousticbrainz but override with user-defined
           values if present'''
        log.info('VIEW: replace key, bpm data with AccousticBrainz data')
        # first convert list of rows to list of dicts:
        table = [dict(row) for row in list_of_rows]
        # now look for acousticbrainz values and replace if necessary
        for i, row in enumerate(table):
            if row['a_key'] and not row['key']:
                if row['a_chords_key'] != row['a_key']:
                    table[i]['key'] = '{}/{}*'.format((row['a_key'],
                                                       row['a_chords_key']))
                else:
                    table[i]['key'] = '{}*'.format((row['a_key']))
            if row['a_bpm'] and not row['bpm']:
                table[i]['bpm'] = '{}*'.format(round(float(row['a_bpm']), 1))
            # in any case remove acousticbrainz fields
            del(table[i]['a_key'])
            del(table[i]['a_chords_key'])
            del(table[i]['a_bpm'])
        return table

# Mix view utils and data, usable in CLI and GUI, related to mixes only
class Mix_view_common(ABC):
    def __init__(self):
        # list of questions a user is asked when editing a mix-track
        # first list item is the related db-field, second is the question
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

# Collection view utils, usable in CLI and GUI, related to Collection only
class Collection_view_common(ABC):
    def __init__(self):
        #super(Collection_view_cli, self).__init__()
        pass

    def d_tracklist_parse(self, d_tracklist, track_number):
        '''gets Track name from discogs tracklist object via track_number, eg. A1'''
        for tr in d_tracklist:
            #log.debug("d_tracklist_parse: this is the tr object: {}".format(dir(tr)))
            #log.debug("d_tracklist_parse: this is the tr object: {}".format(tr))
            if tr.position == track_number:
                return tr.title
        log.debug('d_tracklist_parse: Track {} not existing on release.'.format(
            track_number))
        return False # we didn't find the tracknumber

    def d_tracklist_parse_numerical(self, d_tracklist, track_number):
        '''get numerical track pos from discogs tracklist object via
           track_number, eg. A1'''
        for num, tr in enumerate(d_tracklist):
            if tr.position == track_number:
                return num + 1 # return human readable (matches brainz position)
        log.debug(
            'd_tracklist_parse_numerical: Track {} not existing on release.'.format(
              track_number))
        return False # we didn't find the tracknumber

# common view utils, usable in CLI only
class View_common_cli(ABC):
    def print_help(self, message):
        print(''+str(message)+'\n')

    def ask_user(self, text=""):
        ''' ask user for something and return answer '''
        return input(text)

    def ask_user_for_track(self):
        track_no = self.ask_user("Which track? (A1) ")
        # FIXME a sanity checker, at least for online search, would be nice here.
        # also the default value is not checked, eg it could be A in reality!
        if track_no == '':
            track_no = 'A1'
        return track_no

    def tab_mix_table(self, _mix_data, _verbose = False):
        _mix_data_key_bpm = self.replace_key_bpm(_mix_data)
        _mix_data_nl = self.trim_table_fields(_mix_data_key_bpm)
        for row in _mix_data_nl: # debug only
           log.debug(str(row))
        log.debug("")
        if _verbose:
            self.print_help(tab(_mix_data_nl, tablefmt='pipe',
              headers={'track_pos': '#', 'discogs_title': 'Release',
                       'd_artist': 'Track\nArtist', 'd_track_name': 'Track\nName',
                       'd_track_no': 'Track\nPos', 'key': 'Key', 'bpm': 'BPM',
                       'key_notes': 'Key\nNotes', 'trans_rating': 'Trans.\nRating',
                       'trans_notes': 'Trans.\nR. Notes', 'notes': 'Track\nNotes'}))
        else:
            self.print_help(tab(_mix_data_nl, tablefmt='pipe',
              headers={'track_pos': '#', 'discogs_title': 'Release',
                       'd_track_no': 'Tr\nPos', 'trans_rating': 'Trns\nRat',
                       'key': 'Key', 'bpm': 'BPM'}))

# viewing mixes in CLI mode:
class Mix_view_cli(Mix_view_common, View_common_cli, View_common):
    def __init__(self):
        super(Mix_view_cli, self).__init__()

    def tab_mixes_list(self, mixes_data):
        # make list of dicts out of the sqlite tuples list
        mixes = [dict(row) for row in mixes_data]
        for i, mix in enumerate(mixes): # shorten all created timestamp fields
            mixes[i]['created'] = self.shorten_timestamp(mix['created'],
                  text = True)
            mixes[i]['played'] = self.format_date_month(mix['played'],
                  text = True)
        tabulated = tab(self.trim_table_fields(mixes),
          tablefmt="simple", # headers has to be dict too!
          headers={'mix_id': '#', 'name': 'Name', 'played':'Played',
                   'venue': 'Venue', 'created': 'Created', 'updated': 'Updated'})
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

# viewing collection (search) outputs in CLI mode:
class Collection_view_cli(Collection_view_common, View_common_cli, View_common):
    def __init__(self):
        super(Collection_view_cli, self).__init__()

    def print_found_discogs_release(self, discogs_results, _searchterm, _db_releases):
        ''' formatted output _and return of Discogs release search results'''
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
            try:
                if result_item.id == dbr[0]:
                    #return result_list[0]
                    log.info("Compiled Discogs result_list: {}".format(result_list))
                    return result_list
                    break
            except UnboundLocalError as unb:
                log.error("Discogs collection was not imported to DiscoBASE properly!")
                #raise unb
                raise SystemExit(1)
        return False

    def tab_online_search_results(self, _result_list):
        self.print_help(tab(_result_list, tablefmt="simple",
                  headers=["ID", "Artist", "Release", "Label", "C", "Year", "Format"]))

    def online_search_results_tracklist(self, _tracklist):
        for track in _tracklist:
            print(track.position + "\t" + track.title)
        print()

    def tab_all_releases(self, releases_data):
        #self.print_help(tab(releases_data, tablefmt="plain",
        print(tab(releases_data, tablefmt="plain",
            #headers=["Discogs ID", "Artist", "Release Title", "Last import", "in Collection"]))
            headers=["Discogs ID", "Artist", "Release Title"]))

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

# CLI user interaction class - holds info about what user wants to do
# analyzes argparser args and puts it to nicely human readable properties
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
        self.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE = False
        self.WANTS_VERBOSE_MIX_TRACKLIST = False
        self.WANTS_TO_REORDER_MIX_TRACKLIST = False
        self.WANTS_TO_ADD_AT_POSITION = False
        self.WANTS_TO_DELETE_MIX_TRACK = False
        self.WANTS_TO_ADD_RELEASE_IN_MIX_MODE = False
        self.WANTS_TO_ADD_AT_POS_IN_MIX_MODE = False
        self.WANTS_TO_COPY_MIX = False
        self.WANTS_TO_DELETE_MIX = False
        self.WANTS_SUGGEST_TRACK_REPORT = False
        self.WANTS_TO_BULK_EDIT = False
        self.WANTS_SUGGEST_BPM_REPORT = False
        self.WANTS_SUGGEST_KEY_REPORT = False
        self.WANTS_SUGGEST_BPM_AND_KEY_REPORT = False
        self.WANTS_TO_PULL_BRAINZ_INFO = False
        self.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = False
        self.BRAINZ_SEARCH_DETAIL = 1

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
                if self.args.add_to_mix !=0 and self.args.track_to_add !=0:
                    self.WANTS_TO_ADD_TO_MIX = True
                if self.args.add_to_mix !=0:
                    self.WANTS_TO_ADD_TO_MIX = True

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
                    self.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                if self.args.brainz_update:
                    self.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    self.BRAINZ_SEARCH_DETAIL == self.args.brainz_update
                    if self.args.brainz_update > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2
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
                    self.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                if self.args.delete_mix:
                    self.WANTS_TO_DELETE_MIX = True
                    self.WANTS_ONLINE = False
                if self.args.bulk_edit:
                    self.WANTS_TO_BULK_EDIT = True
                if self.args.brainz_update:
                    self.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    self.BRAINZ_SEARCH_DETAIL == self.args.brainz_update
                    if self.args.brainz_update > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2


        # SUGGEST MODE
        if hasattr(self.args, 'suggest_search'):
            self.WANTS_TO_SUGGEST_SEARCH = True
            log.debug("Entered suggestion mode.")
            if (self.args.suggest_bpm and self.args.suggest_search == "0"
                  and self.args.suggest_key):
                log.debug("Entered BPM and key suggestion report.")
                self.WANTS_SUGGEST_BPM_AND_KEY_REPORT = True
            elif (self.args.suggest_bpm and self.args.suggest_search is not "0"
                  and self.args.suggest_key):
                log.error("You can't combine BPM and key with Track-combination report.")
                raise SystemExit(1)
            elif self.args.suggest_bpm and self.args.suggest_search is not "0":
                log.error("You can't combine BPM with Track-combination report.")
                raise SystemExit(1)
            elif self.args.suggest_key and self.args.suggest_search is not "0":
                log.error("You can't combine key with Track-combination report.")
                raise SystemExit(1)
            elif self.args.suggest_bpm and self.args.suggest_search == "0":
                log.debug("Entered BPM suggestion report.")
                self.WANTS_SUGGEST_BPM_REPORT = True
            elif self.args.suggest_key and self.args.suggest_search == "0":
                log.debug("Entered musical key suggestion report.")
                self.WANTS_SUGGEST_KEY_REPORT = True
            elif self.args.suggest_search == "0":
                log.debug("Entered Track-combination report. No searchterm.")
            else:
                log.debug("Entered Track-combination report.")
                self.WANTS_SUGGEST_TRACK_REPORT = True
            #log.error("track search not implemented yet.")
            #raise SystemExit(1)

        if self.args.offline_mode == True:
            self.WANTS_ONLINE = False


class main_frame():
    def __init__(self, conn=False):

        self.start_up = True

        log.debug("############################################################")
        log.debug("###########DISCODOS#LOG#START##############################")
        log.debug("############################################################")
        self.search_open = False
        self.main_win = tk.Tk()  

        image = Image.open("assets/editor.png")
        self.background_image = ImageTk.PhotoImage(image)
        
        

        self.main_win.geometry("1200x700")     
        self.main_win.minsize(1200, 700)

        
        

        self.main_win.title("Discodos") # TODO: Add relevant Information to title, like Titles in Mix etc
        self.conn = conn

        ########################################## GUI CONTROLLER
        
        

        # Create all Widgets, outsourced to its own function
        self.create_lists()
        self.gui_ctrl = ctrls.mix_ctrl_gui( self.conn, 
                                            self.mix_cols, 
                                            self.track_cols, 
                                            self.mix_list, 
                                            self.tracks_list,
                                            self.start_up)

        self.editor_funcs=   {
                            "save_track" : self.gui_ctrl.save_track_data,
                            "save_mix" : self.gui_ctrl.save_mix_data,
                            "delete_mix" : self.gui_ctrl.delete_selected_mix,
                            "remove_track" : self.gui_ctrl.remove_track_from_mix,
                            "move_track" : self.gui_ctrl.move_track_pos
                            }


        self.search_funcs = [
                '''self.gui_ctrl.display_searched_releases((self.artist_bar.get(), 
                                                        self.release_bar.get(),
                                                        self.track_bar.get()),
                                                        self.search_tv,
                                                        self.online.get())'''
                                    ]


        self.create_toolbars()
        self.search_tv_config()
        self.gui_ctrl.display_all_mixes()
        self.show_tracklist()
        self.spawn_editor("start")
        

        
                    
    # Exit GUI cleanly
    def _quit(self):
        self.main_win.quit()
        self.main_win.destroy()
        exit() 

    # Instantiate the DB-Connector and load the Data


# EVENT TRIGGER UNCTION - UPDATE TRACK LIST            
        
    def show_tracklist(self):
        self.gui_ctrl.display_tracklist(self.mix_list.item(self.mix_list.focus(),"text"))
        self.spawn_editor(0)


    
    #############################################################
    # COLUMN SORTING FUNCTION
    ############################################################

    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        # reverse sort next time
        self.mix_list.heading(col, command=lambda _col=col: self.treeview_sort_column(tv, _col, not reverse))


    #####################################################################################    
    # CREATE WIDGETS
    ######################################################################

    def create_lists(self):

        self.mix_frame = tk.LabelFrame(self.main_win, text="Mixes")
        self.tracks_frame = tk.LabelFrame(self.main_win, text="Tracks in Mix")

        ########################################################################

        # MIXES LISTVIEW

        self.mix_list = ttk.Treeview(self.mix_frame)
        self.mix_list.pack(fill="both", expand=1)
        self.mix_list['show'] = 'headings'

        # TRACKS LISTVIEW

        self.tracks_list = ttk.Treeview(self.tracks_frame)
        self.tracks_list.pack(fill="both", expand=1)
        self.tracks_list['show'] = 'headings'

        # CREATING ALL COLUMNS

        self.mix_cols = {
                        "mix_id" : "Mix #", 
                        "name" : "Name", 
                        "venue" : "Venue", 
                        "played" : "Played"                        
                        # "created" : "Created", 
                        # "updated" : "Updated"
                        }

        self.track_cols = {
                            "track_pos" : "#", 
                            "artist" : "Artist", 
                            "track" : "Track Name", 
                            "key" : "Key", 
                            "bpm" : "Bpm", 
                            "keynotes" : "Key Notes", 
                            "transr" : "Trans. Rating", 
                            "transnotes" : "Trans. Notes", 
                            "notes" : "Notes"
                            }


        self.mix_list["columns"] = tuple(self.mix_cols)
        self.tracks_list["columns"] = tuple(self.track_cols)


        for col_id, heading in self.mix_cols.items():
            self.mix_list.column(col_id, width=2, stretch=1)
            self.mix_list.heading(col_id,text=heading, anchor=tk.W, command=lambda _col=col_id: self.treeview_sort_column(self.mix_list, _col, False))


        for col_id, heading in self.track_cols.items():
            self.tracks_list.column(col_id, width=2, stretch=1)
            self.tracks_list.heading(col_id, text=heading,anchor=tk.W)

        self.mix_list.bind('<<TreeviewSelect>>', lambda a : self.show_tracklist())
        self.tracks_list.bind('<<TreeviewSelect>>', lambda a : self.spawn_editor(1))


    ####################################
    # EDITOR
    ###################################

    def spawn_editor(self, editor_view):

        ########### PREPARATION ###############

        self.editor_frame = tk.LabelFrame(self.main_win, text="Editor")
        self.move_frame = tk.Frame(self.editor_frame)

        try: 
            for name, lst in self.editor_entries.items():
                for elem in lst:
                        elem.destroy()
        except:
            pass
           
        


        ############### SWITCH ###################

        self.editor_entries = {
            "labels" : [],
            "entries": [],
            "buttons": []
        }

        if editor_view == 0:
            show_entries = True
            headings = list(self.mix_cols.values())
            data = self.mix_list.item(self.mix_list.focus())


            self.editor_entries["buttons"].append([
                tk.Button(self.editor_frame, text="Save Mix", command=lambda : self.editor_funcs["save_mix"]( self.editor_entries["entries"],
                                                                                                                 self.mix_list.item(self.mix_list.focus(),"text"))),
                tk.Button(self.editor_frame, text="Delete Mix", command=lambda : self.editor_funcs["delete_mix"](self.mix_list.item(self.mix_list.focus(),"text")))
            ])


        elif editor_view == 1:
            show_entries = True
            headings = list(self.track_cols.values()) 
            data = self.tracks_list.item(self.tracks_list.focus())

            self.editor_entries["buttons"].append([
                tk.Button(self.editor_frame, text="Save Track", command=lambda : self.editor_funcs["save_track"](  self.editor_entries["entries"],
                                                                                                                    self.mix_list.item(self.mix_list.focus(),"text"))),
                tk.Button(self.editor_frame, text="Remove Track", command=lambda : self.editor_funcs["remove_track"]( self.mix_list.item(self.mix_list.focus(),"text"), 
                                                                                                                data["values"][0])),
                tk.Button(self.move_frame, text="^", command=lambda : self.editor_funcs["move_track"]( self.mix_list.item(self.mix_list.focus(),"text"), 
                                                                                                                data["values"][0],
                                                                                                                "up")),
                tk.Button(self.move_frame, text="V", command=lambda : self.editor_funcs["move_track"]( self.mix_list.item(self.mix_list.focus(),"text"), 
                                                                                                                data["values"][0],
                                                                                                                "down"))
            ])
            
        elif editor_view == 2:
            show_entries = True
            headings = list(self.mix_cols.values())
            data = {}
            data["values"] = []
            for elem in headings:  
                data["values"].append("")

            self.editor_entries["buttons"].append([
                tk.Button(self.editor_frame, text="Save New Mix", command=lambda : self.editor_funcs["save_mix"](self.editor_entries["entries"],
                                                                                                        self.mix_list.item(self.mix_list.focus(),"text")))
            ])
        
        elif editor_view == "start":
            editor_image = tk.Label(self.editor_frame, image=self.background_image)
            editor_image.grid(row=0, column=0, sticky="nsew")
            headings = []
            data = {}
            data["values"] = []



        ######### DESTILLERY ###########

        try:
            for i, val  in enumerate(data["values"]):
                lab = tk.Label(self.editor_frame, text=headings[i])
                lab.grid(row=i, column=0, sticky="w")
                self.editor_entries["labels"].append(lab)
                en = tk.Entry(self.editor_frame)
                en.grid(row=i, column=1, sticky="w")
                
                en.insert(0, data["values"][i])
                self.editor_entries["entries"].append(en)

                
        except:
            pass

        ######## WHICH ENTRIES ARE DISABLED ###########
        
        for i, en in enumerate(self.editor_entries["entries"]):
            if editor_view == 0:
                self.editor_entries["entries"][0].config(state='disabled')
            elif editor_view == 1:  
                if i == 0 or i == 1 or i == 2:
                    self.editor_entries["entries"][i].config(state='disabled')

        ########### BUTTONS ###########
        
        if data["values"] != "":
            col_count = 0
            row_count = 2
            for lst in self.editor_entries["buttons"]:
                for obj in lst:
                    if col_count == 1:
                        count = 0
                    obj.grid(row=len(self.editor_entries["entries"])+row_count, column=col_count, sticky="w")
                    if col_count == 1:
                        row_count += 1
                    col_count += 1


        ########### SHOW ##############

        if editor_view == 1:
            self.move_frame.grid(row=len(self.editor_entries["entries"])+1, column=1, sticky="w")

        self.editor_frame.grid(row=0, column=5, columnspan=5, rowspan=5, sticky="news")
            

    def create_toolbars(self):

        #########################################################################

        # STATUS BAR

        self.status=tk.StringVar()  
        self.status_bar = tk.Label(self.main_win, textvariable=self.status, anchor=tk.W, bd=1, relief=tk.SUNKEN)
        

        self.status.set("Ready...")

        #########################################################################
        # BUTTON AREA
        #########################################################################

        self.toolbox = tk.LabelFrame(self.main_win, text="Toolbox")
        
        self.new_mix_btn = tk.Button(self.toolbox, text="New Mix", command=lambda: self.spawn_editor(2))
        self.new_mix_btn.grid(row=0, column=0, sticky="w")

        #######################################################
        # SEARCH AREA
        ##################################################################

        self.search_frame = ttk.LabelFrame(self.main_win, text="Search Releases")

        self.bar_grid = tk.Frame(self.search_frame)

        tk.Label(self.bar_grid, text="Artist").grid(row=0, column=0, sticky="e")
        self.artist_bar = tk.Entry(self.bar_grid)
        self.artist_bar.grid(row=0, column=1, columnspan=3, rowspan=1, sticky="we")

        tk.Label(self.bar_grid, text="Release").grid(row=1, column=0, sticky="e")
        self.release_bar = tk.Entry(self.bar_grid)
        self.release_bar.grid(row=1, column=1, columnspan=3, rowspan=1, sticky="we")

        tk.Label(self.bar_grid, text="Track").grid(row=2, column=0, sticky="e")
        self.track_bar = tk.Entry(self.bar_grid)
        self.track_bar.grid(row=2, column=1, columnspan=3, rowspan=1, sticky="we")

        self.bar_grid.grid(row=0, column=0, rowspan=4, columnspan=3, sticky="nw")

        self.online = tk.IntVar()
        tk.Checkbutton(self.bar_grid, text="online", variable=self.online).grid(row=0, column=4, sticky="ne")

        self.search_button = tk.Button(self.bar_grid, 
                                        text="Search...", 
                                        command=lambda:eval(self.search_funcs[0]))
        self.search_button.grid(row=4, column=0, sticky="we", columnspan=3)

        self.artist_bar.bind("<Return>", lambda x:eval(self.search_funcs[0]))
        self.release_bar.bind("<Return>", lambda x:eval(self.search_funcs[0]))
        self.track_bar.bind("<Return>", lambda x:eval(self.search_funcs[0]))

        # SEARCH TREEVIEW

        self.search_tv = ttk.Treeview(self.search_frame)
        self.search_tv.grid(row=4, column=0, columnspan=15, rowspan=8, sticky="nsew")

        
        # SEARCH TOOLS
        ###############

        self.search_tools = tk.Frame(self.search_frame)
        self.add_btn = tk.Button(self.search_tools, text="Add Track to Mix", state="disabled", 
                                                    command = lambda : self.gui_ctrl.add_track_to_mix(self.search_tv)) 
        self.add_btn.grid(row=0, column=0, sticky="ws")

        self.search_tools.grid(row=12, column=0, sticky="nsew")

        self.pg_bar = ttk.Progressbar(self.search_frame, orient="horizontal", mode='indeterminate')
        self.pg_bar.grid(row=15, column=0, columnspan=15, rowspan=1, sticky="we")
        

        # DISPLAY
           
        self.status_bar.grid(row=15, column=0, columnspan=15, rowspan=1, sticky="wes")
        self.mix_frame.grid(row=0, column=0, columnspan=5, rowspan=5, sticky="nwes")
        self.tracks_frame.grid(row=5, column=0, columnspan=7, rowspan=10, sticky="swen")
        self.toolbox.grid(row=5, column=7, columnspan=3,rowspan=10, sticky="sewn")
        self.search_frame.grid(row=0, column=10, columnspan=5, rowspan=15, sticky="nsew")

        # WEIGHTS

        for i in range(15):
                self.main_win.rowconfigure(i, weight=1)
                self.main_win.columnconfigure(i, weight=1)
                self.search_frame.columnconfigure(i, weight=1)
                self.search_frame.rowconfigure(i, weight=1)

    
    def search_tv_config(self):
        # self.search_tv['show'] = 'headings'
        self.search_cols = {
                        "1" : "", 
                        "2" : "", 
                        "3" : "", 
                        "4" : "" 
                        }

        self.search_tv["columns"] = tuple(self.search_cols)

        self.search_tv.column('#0', width=20, stretch=0)
        
        for col_id, heading in self.search_cols.items():
            self.search_tv.column(col_id, width=5, stretch=1)
            self.search_tv.heading(col_id,text=heading, anchor="w")
        
        self.search_tv.bind('<<TreeviewSelect>>', lambda a : self.search_tools_config())



    def search_tools_config(self):
        if self.add_btn['state'] == "disabled":
            self.add_btn.config(state='normal')
            self.pos_entry.config(state='normal')

    
    def progress(self, currentValue):
        pg_bar["value"]=currentValue
            

class setup_frame():
    def __init__(self, conn=False):

        self.setup_win = tk.Tk()  

        # self.setup_win.geometry("300x200")     
        # self.setup_win.minsize(300, 200)
        self.setup_win.resizable(False, False)  

        self.setup_win.title("Discodos Setup GUI") 
        self.conn = conn
        self.setup_ctrl = ctrls.setup_controller(self.conn)

        self.create_interface()
    
    
    def create_interface(self):
        labels = ["Discogs Token", "Discogs AppID", "Log Level"]
        self.entries = {key: None for key in labels}
        i = 0
        for label, entry in self.entries.items():
            self.entries[label] = tk.Entry(self.setup_win)
            self.entries[label].grid(row=i, column=1, sticky="we")
            tk.Label(self.setup_win, text=label).grid(row=i, column =0, sticky="we")
            i += 1
        
        self.btn_frame = tk.Frame(self.setup_win)

        self.start_setup_btn = tk.Button(self.btn_frame, text="Start Setup")
        self.start_setup_btn.grid(row=0, column=0, sticky="w")
        # When Done, change this Button text to "Done!"
        tk.Button(self.btn_frame, text="Cancel").grid(row=0, column=1, sticky="w")

        

        self.btn_frame.grid(row=len(self.entries)+1, column=1, sticky="w")

        self.log_window = tk.Text(self.setup_win, width=40, height=5)
        self.log_window.grid(row=len(self.entries)+2, column=0, columnspan=2, sticky="wens")

        self.log_window.insert(tk.END,"Logging...")
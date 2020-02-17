###############################
########
# TODO #
########

########## COLUMN WIDTH ###############
# Refactoring of Column width detectors.
# Make List of Column headings (or dict?)
# create columns with for loop per item in list
# -> OR: Make Dict
# Mix_Data{"Heading1": ["Value1", "Value2"], "Heading2": ["Value1", "Value2"]}

###########


################################
# IMPORTS
import discodos.views as views
import discodos.ctrls as ctrls
import discodos.models as models
import discodos.utils as utils
import discodos.log as log
from discodos.widgets import edit_mix_view
from discodos.widgets import add_mix_view
from discodos.widgets import edit_track_info

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from tabulate import tabulate as tab


#################################

class main_frame():
    def __init__(self, conn=False):
        log.debug("############################################################")
        log.debug("###########DISCODOS#LOG#START##############################")
        log.debug("############################################################")

        self.main_win = tk.Tk()                           
        self.main_win.geometry("800x600")     
        self.main_win.minsize(800, 600)

        self.main_win.title("Discodos") # TODO: Add relevant Information to title, like Titles in Mix etc
        self.conn = conn

        ########################################## GUI CONTROLLER
        
        

        # Create all Widgets, outsourced to its own function
        self.create_lists()
        self.gui_ctrl = ctrls.mix_ctrl_gui( self.conn, 
                                            self.mix_cols, 
                                            self.track_cols, 
                                            self.mix_list, 
                                            self.tracks_list)

        self.create_toolbars()
        self.focus_first_object(self.mix_list)
        self.gui_ctrl.display_all_mixes()
        self.show_tracklist()

                    
    # Exit GUI cleanly
    def _quit(self):
        self.main_win.quit()
        self.main_win.destroy()
        exit() 

    # Instantiate the DB-Connector and load the Data


# EVENT TRIGGER UNCTION - UPDATE TRACK LIST            
        
    def show_tracklist(self):
        sel_mix = self.mix_list.focus()
        self.gui_ctrl.display_tracklist(self.mix_list.item(sel_mix,"text"))

        try:
            start_child_id_two = self.tracks_list.get_children()[0]
            self.tracks_list.selection_set(start_child_id_two)
            log.debug("GUI: Set Focus on first Track Item")

        except:
            log.error("GUI: Couldn't Set Focus on Track Item")
            self.status.set("Couldn't Set Focus on Track Item")



    def focus_first_object(self, tree_view):
        try:
            start_child_id = self.mix_list.get_children()[0]
            self.mix_list.focus(start_child_id)
            self.mix_list.selection_set(start_child_id)

            log.debug("GUI: Set Focus on first Mix Item")

        except:
            log.error("GUI: Couldn't Set Focus on Mix Item")
            self.status.set("Couldn't Set Focus on Mix Item")




#################################################
############## WIDGET WINDOW SWITCH #############
#################################################  


    def open_widget(self, view):


        # This function gets called, when the user opens up a window.
        # Depending on the Button he presses, the selector chooses wich window will be opened.
        # They are all inherite from the same base-window class.

# OPEN EDIT MIX WINDOW

        if view == "edit_mix":

            cur_sel_mix = self.mix_list.focus()

            try:
                mix = models.Mix(self.conn, self.mix_list.item(cur_sel_mix,"text")) 
                log.debug("GUI: Retrieved Mix Info")   
                self.status.set("Retrieved Mix Info")
                
            except: 
                log.error("GUI: Getting Mix Data failed")
                self.status.set("Getting Mix Data failed")  
                
            try:
                if self.mix_edit_win.win_state == "normal" and cur_sel_mix is self.mix_list.focus(): 
                    log.debug("GUI: Focused Mix Edit Window") 
                    self.mix_edit_win.edit_win.focus()

                elif self.mix_edit_win.win_state == "normal" and cur_sel_mix is not self.mix_list.focus():
                    log.debug("GUI: Reloaded Mix Edit Window") 
                    
                    self.mix_edit_win._quit()
                    self.mix_edit_win = edit_mix_view(self.main_win, mix)
                    self.mix_edit_win.edit_win.focus()
                
                else:
                    self.mix_edit_win = edit_mix_view(self.main_win, mix) 
            
            except:
                self.mix_edit_win = edit_mix_view(self.main_win, mix) 
                self.mix_edit_win.edit_win.focus()

            log.debug("GUI: Mix Window State is " + self.mix_edit_win.win_state)

            self.mix_edit_win.edit_win.protocol("WM_DELETE_WINDOW", self.update_mix_list)
            
            
            # if self.mix_edit_win.edit_win.winfo_exists() == 0:
            # self.mix_edit_win = edit_mix_view(self.main_win, mix)

        
# OPEN CREATE NEW MIX WINDOW
        
        elif view == "add_mix":
            try:
                if self.add_mix_win.win_state == "normal":
                    self.add_mix_win.edit_win.focus()
                    log.debug("GUI: Mix Window State is " + self.add_mix_win.win_state)

                else:
                    self.add_mix_win = add_mix_view(self.main_win, self.conn)
                    self.add_mix_win.edit_win.focus()
            
            except:
                self.add_mix_win = add_mix_view(self.main_win, self.conn)
                self.add_mix_win.edit_win.focus()
            
            # self.add_mix_win.edit_win.protocol("WM_DELETE_WINDOW", self.update_mix_list)
        
# OPEN TRACK EDIT WINDOW
            
        elif view == "track_edit":

            cur_track = self.tracks_list.focus()
            cur_mix = self.mix_list.focus()
            mix = models.Mix(self.conn, self.mix_list.item(cur_mix,"text"))
            try:
                # track = models.Mix(self.conn, self.tracks_list.item(cur_track,"track_pos")) 
                track_data = self.tracks_list.item(cur_track)
                # print(track_data["values"][0])
                log.debug("GUI: Retrieved Track Info")   
                self.status.set("Retrieved Track Info") 
                
                # ############## # # # # # # # # # #
                try:
                    if self.track_edit_win.win_state == "normal" and cur_track is self.tracks_list.focus(): 
                        log.debug("GUI: Focused Track Edit Window") 
                        self.track_edit_win.edit_win.focus()

                    elif self.track_edit_win.win_state == "normal" and cur_track is not self.track_list.focus():
                        log.debug("GUI: Reloaded Track Edit Window") 
                        # RELOAD THE WINDOW WITH CURRENT DATA
                        self.track_edit_win._quit()
                        self.track_edit_win = edit_track_info(self.main_win, track_data, mix)
                        self.track_edit_win.edit_win.focus()

                    log.debug("GUI: Track Window State is " + self.track_edit_win.win_state)

                except:
                    self.track_edit_win = edit_track_info(self.main_win, track_data, mix)  
                    log.debug("GUI: Track Window State is " + self.track_edit_win.win_state) 

            except: 
                log.error("GUI: Getting Track Data failed.")
                self.status.set("Getting Track Data failed")  
            
            
            # self.track_edit_win.edit_win.protocol("WM_DELETE_WINDOW", self.update_track_list)


####################################################################
    ########## DELETE MIX ##########################################

    def delete_mix(self):
        self.gui_ctrl.delete_selected_mix(self.mix_list.item(self.mix_list.focus(),"text"))
        self.update_mix_list()



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
                        "played" : "Played", 
                        "venue" : "Venue", 
                        "created" : "Created", 
                        "updated" : "Updated"
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
        
        self.new_mix_btn = tk.Button(self.toolbox, text="New Mix", command=lambda: self.open_widget("add_mix"))
        self.edit_mix_btn = tk.Button(self.toolbox, text="Edit Mix", command=lambda: self.open_widget("edit_mix"))
        self.del_mix_btn = tk.Button(self.toolbox, text="Delete Mix", command=self.delete_mix)
        self.edit_track_btn = tk.Button(self.toolbox, text="Edit Track Info", command=lambda: self.open_widget("track_edit"))
        self.rmv_track_btn = tk.Button(self.toolbox, text="Remove Track")
        

        self.new_mix_btn.grid(row=0, column=0, sticky="W")
        self.edit_mix_btn.grid(row=0, column=1, sticky="W")
        self.del_mix_btn.grid(row=1, column=0, sticky="W")
        self.edit_track_btn.grid(row=0, column=1, sticky="W")
        self.rmv_track_btn.grid(row=2, column=0, sticky="W")

        ###########################
        # EDITOR
        ########################

        self.editor_frame = tk.LabelFrame(self.main_win, text="Editor")
        for i in range(5):
            for j in range(2):
                tk.Entry(self.editor_frame, width=30).grid(row=i, column=j, sticky="w")



        #########
        # SEARCH TOGGLE BUTTON
        self.search_toggle = tk.Button(self.main_win, text = ">") 
        
   



        # DISPLAY
           
        self.status_bar.grid(row=10, column=0, columnspan=10, rowspan=1, sticky="we")
        self.mix_frame.grid(row=0, column=0, columnspan=5, rowspan=5, sticky="nwes")
        self.editor_frame.grid(row=0, column=5, columnspan=5, rowspan=5, sticky="news")
        self.tracks_frame.grid(row=5, column=0, columnspan=7, rowspan=4, sticky="swen")
        self.toolbox.grid(row=5, column=7, columnspan=3,rowspan=4, sticky="sewn")
        self.search_toggle.grid(row=0, column=11, columnspan=1,rowspan=11, sticky="sn")
        
        # WEIGHTS

        for i in range(11):
            self.main_win.columnconfigure(i, weight=1)
            self.main_win.rowconfigure(i, weight=1)
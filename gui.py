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
from discodos import views
from discodos import ctrls
from discodos import models
from discodos import utils
from discodos import log
from discodos.widgets import edit_mix_view
from discodos.widgets import add_mix_view
from discodos.widgets import edit_track_info
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from tabulate import tabulate as tab


#################################

class main_frame():
    def __init__(self):

        log.debug("############################################################")
        log.debug("###########DISCODOS#LOG#START##############################")
        log.debug("############################################################")

        self.main_win = tk.Tk()                           
        self.main_win.geometry("800x600")     
        # self.main_win.resizable(False, False) 

        self.main_win.title("Discodos") # EDIT: Add relevant Information to title, like Titles in Mix etc

        # Create all Widgets, outsourced to its own function
        self.create_widgets()
        self.mix_starter()

                    
    # Exit GUI cleanly
    def _quit(self):
        self.main_win.quit()
        self.main_win.destroy()
        exit() 

    # Instantiate the DB-Connector and load the Data

    def mix_starter(self):
        self.discodos_root = Path(os.path.dirname(os.path.abspath(__file__)))
        # conf = utils.read_yaml(discodos_root / "config.yaml")
        self.discobase = self.discodos_root / "discobase.db"
        # CONFIGURATOR INIT: db and config file handling, DISCOGS API conf
        self.conf = utils.Config()
        



        self.update_mix_list()
        self.mix_list.bind('<<TreeviewSelect>>', self.show_mix)
        self.focus_first_object()


# EVENT TRIGGER UNCTION - UPDATE TRACK LIST            
        
    def show_mix(self, event):
        self.update_track_list()



    def focus_first_object(self):
        try:
            start_child_id = self.mix_list.get_children()[0]
            self.mix_list.focus(start_child_id)
            self.mix_list.selection_set(start_child_id)

            log.debug("GUI: Set Focus on first Mix Item")

        except:
            log.error("GUI: Couldn't Set Focus on Mix Item")
            self.status.set("Couldn't Set Focus on Mix Item")

# UPDATE THE TRACK LIST WITHOUT EVENT

    def update_track_list(self):
        # This function gets called, when the user selects a mix in the List of Mixes
        # Here we fetch the selected Mix in the Mix Treeview 
        curItem = self.mix_list.focus()
        try:
            mix = models.Mix(self.conn, self.mix_list.item(curItem,"text"))
            # print(self.mix_list.item(curItem,"text"))
            
            mix_data = mix.get_full_mix(verbose = True) 
            log.debug("GUI: Retrieved Mix data")   
            self.status.set("Retrieved Mix data") 

        except: 
            mix_data = []
            log.error("GUI: Getting Mix Data failed")
            self.status.set("Getting Mix Data failed")  
        
        
        ########################################################

        # Here is the same game for the track width values
        # We create a Dictionary


        

        
        self.tracks_list.delete(*self.tracks_list.get_children())

        track_width_vals = {}     
        track_width_vals["track_pos_width"] = []
        track_width_vals["d_artist_width"] = []
        track_width_vals["d_track_name_width"] = []
        track_width_vals["key_width"] = []
        track_width_vals["bpm_width"] = []
        track_width_vals["key_notes_width"] = []
        track_width_vals["trans_rating_width"] = []
        track_width_vals["trans_notes_width"] = []
        track_width_vals["notes_width"] = []

        for i, row in enumerate(mix_data):

            # print(dir(row["track_pos"]))

            try:

                self.tracks_list.insert("", i, text="", values=(utils.none_checker(row["track_pos"]), 
                                                                utils.none_checker(row["d_artist"]), 
                                                                utils.none_checker(row["d_track_name"]), 
                                                                utils.none_checker(row["key"]), 
                                                                utils.none_checker(row["bpm"]), 
                                                                utils.none_checker(row["key_notes"]), 
                                                                utils.none_checker(row["trans_rating"]), 
                                                                utils.none_checker(row["trans_notes"]), 
                                                                utils.none_checker(row["notes"])))

            
                try:
                    track_width_vals["track_pos_width"].append(tkfont.Font().measure(row["track_pos"]))
                except:
                    track_width_vals["track_pos_width"].append(5)
                    log.debug("GUI: Track Position width not fetched. Set default value 5.")

                try:
                    track_width_vals["d_artist_width"].append(tkfont.Font().measure(row["d_artist"]))
                except:
                    track_width_vals["d_artist_width"].append(5)
                    log.debug("GUI: Artist width not fetched. Set default value 5.")

                try:
                    track_width_vals["d_track_name_width"].append(tkfont.Font().measure(row["d_track_name"]))
                except:
                    track_width_vals["d_track_name_width"].append(5)
                    log.debug("GUI: Track Name width not fetched. Set default value 5.")

                try:
                    track_width_vals["key_width"].append(tkfont.Font().measure(row["key"]))
                except:
                    track_width_vals["key_width"].append(5)
                    log.debug("GUI: Key width not fetched. Set default value 5.")

                try:
                    track_width_vals["bpm_width"].append(tkfont.Font().measure(row["bpm"]))
                except:
                    track_width_vals["bpm_width"].append(5)
                    log.debug("GUI: BPM width not fetched. Set default value 5.")

                try:
                    track_width_vals["key_notes_width"].append(tkfont.Font().measure(row["key_notes"]))
                except:
                    track_width_vals["key_notes_width"].append(5)
                    log.debug("GUI: Key Notes width not fetched. Set default value 5.")   

                try:
                    track_width_vals["trans_rating_width"].append(tkfont.Font().measure(row["trans_rating"]))
                except:
                    track_width_vals["trans_rating_width"].append(5)
                    log.debug("GUI: Trans Rating width not fetched. Set default value 5.")   

                try:
                    track_width_vals["trans_notes_width"].append(tkfont.Font().measure(row["trans_notes"]))
                except:
                    track_width_vals["trans_notes_width"].append(7)
                    log.debug("GUI: Trans Notes width not fetched. Set default value 7.")   

                try:
                    track_width_vals["notes_width"].append(tkfont.Font().measure(row["notes"]))
                except:
                    track_width_vals["notes_width"].append(5)
                    log.debug("GUI: Notes width not fetched. Set default value 5.")                  
                
                log.debug("GUI: Inserted Track row")
                self.status.set("Inserted Track row") 

            except:

                log.error(f"GUI: Inserting Track Row failed {row['d_artist']}")
                self.status.set(f"GUI: Inserting Track Row failed {row['d_artist']}") 
                

        try:
            start_child_id_two = self.tracks_list.get_children()[0]
            self.tracks_list.selection_set(start_child_id_two)
            log.debug("GUI: Set Focus on first Track Item")

        except:
            log.error("GUI: Couldn't Set Focus on Track Item")
            self.status.set("Couldn't Set Focus on Track Item")
        
        # print(track_width_vals["track_pos_width"])

        self.tracks_list.column("track_pos", width=max(utils.none_checker(track_width_vals["track_pos_width"])), minwidth=tkfont.Font().measure("#"), stretch=1)
        self.tracks_list.column("artist", width=max(utils.none_checker(track_width_vals["d_artist_width"])), minwidth=tkfont.Font().measure("Artist"), stretch=1)
        # print(max(utils.none_checker(track_width_vals["track_id_width"])))
        self.tracks_list.column("track", width=max(utils.none_checker(track_width_vals["d_track_name_width"])), minwidth=tkfont.Font().measure("Track Name"), stretch=1)
        self.tracks_list.column("key", width=max(utils.none_checker(track_width_vals["key_width"])), minwidth=tkfont.Font().measure("Key"), stretch=1)
        self.tracks_list.column("bpm", width=max(utils.none_checker(track_width_vals["bpm_width"])), minwidth=tkfont.Font().measure("BPM"), stretch=1)
        self.tracks_list.column("keynotes", width=max(utils.none_checker(track_width_vals["key_notes_width"])), minwidth=tkfont.Font().measure("Key Notes"), stretch=1)
        self.tracks_list.column("transnotes", width=max(utils.none_checker(track_width_vals["trans_notes_width"])), minwidth=tkfont.Font().measure("Trans. Notes"), stretch=1)
        self.tracks_list.column("transr", width=max(utils.none_checker(track_width_vals["trans_rating_width"])), minwidth=tkfont.Font().measure("Trans. Rating"), stretch=1)
        self.tracks_list.column("notes", width=max(utils.none_checker(track_width_vals["notes_width"])), minwidth=tkfont.Font().measure("Notes"), stretch=1)
        self.tracks_list.column("d_release_id", width=max(utils.none_checker(track_width_vals["bpm_width"])), minwidth=tkfont.Font().measure("Mix Track ID"), stretch=1)




# UPDATE THE MIX LIST 

    def update_mix_list(self):

        self.db_obj = models.Database(db_file = self.conf.discobase)

        ################################################## DB CONN

        try:
            self.conn = self.db_obj.db_conn
            log.info("GUI: DB Connection Success")
            self.status.set("DB Connection Success")
        except:
            log.error("GUI: DB Connection Failed")
            self.status.set("DB Connection Failed")

        #################################################


        self.db_obj = models.Database(db_file = self.discobase)

        self.all_mix = models.Mix(self.conn, "all")
        self.mixes_data = self.all_mix.get_all_mixes()

        self.mix_list.delete(*self.mix_list.get_children())

        self.mix_width_vals = {}     
        self.mix_width_vals["mix_id_width"] = []
        self.mix_width_vals["name_width"] = []
        self.mix_width_vals["played_width"] = []
        self.mix_width_vals["venue_width"] = []
        self.mix_width_vals["created_width"] = []
        self.mix_width_vals["updated_width"] = []

        for i, row in enumerate(self.mixes_data):
            try:
                # Here, the "text"-value is also set with the mix-id, so we can fetch it 
                # later when we get the tracklist
                # The "text"-column is not shown, it serves just as ID
                self.mix_list.insert("" , i, text=row["mix_id"], 
                                            values=(utils.none_checker(row["mix_id"]), 
                                                    utils.none_checker(row["name"]), 
                                                    utils.none_checker(row["played"]), 
                                                    utils.none_checker(row["venue"]), 
                                                    utils.none_checker(row["created"]), 
                                                    utils.none_checker(row["updated"])))
                
                try:
                    self.mix_width_vals["mix_id_width"].append(tkfont.Font().measure(row["mix_id"]))
                except:
                    self.mix_width_vals["mix_id_width"].append(3)
                    log.debug("GUI: Mix ID width not fetched. Set default value 3.")
                try:
                    self.mix_width_vals["name_width"].append(tkfont.Font().measure(row["name"]))
                except:
                    self.mix_width_vals["name_width"].append(3)
                    log.debug("GUI: Name width not fetched. Set default value 3.")
                try:
                    self.mix_width_vals["played_width"].append(tkfont.Font().measure(row["played"]))
                except:
                    self.mix_width_vals["played_width"].append(3)
                    log.debug("GUI: Played width not fetched. Set default value 3.")
                try:
                    self.mix_width_vals["venue_width"].append(tkfont.Font().measure(row["venue"]))
                except:
                    self.mix_width_vals["venue_width"].append(3)
                    log.debug("GUI: Venue width not fetched. Set default value 3.")
                try:
                    self.mix_width_vals["created_width"].append(tkfont.Font().measure(row["created"]))
                except:
                    self.mix_width_vals["created_width"].append(3)
                    log.debug("GUI: created width not fetched. Set default value 3.")
                try:
                    self.mix_width_vals["updated_width"].append(tkfont.Font().measure(row["updated"]))
                except:
                    self.mix_width_vals["updated_width"].append(3)
                    log.debug("GUI: Updated width not fetched. Set default value 3.")


                log.debug("GUI: Inserted Mix Row")
                self.status.set("Inserted Mix Row")

            except:
                log.error("GUI: Inserting Mix Row failed")
                self.status.set("Inserting Mix Row failed")
        
        self.mix_list.column("mix_id_col", width=max(self.mix_width_vals["mix_id_width"]), minwidth=tkfont.Font().measure("Mix #"), stretch=1)
        self.mix_list.column("name", width=max(self.mix_width_vals["mix_id_width"]), minwidth=tkfont.Font().measure("Name"), stretch=1)
        self.mix_list.column("played", width=max(self.mix_width_vals["played_width"]), minwidth=tkfont.Font().measure("Played"), stretch=1)
        self.mix_list.column("venue", width=max(self.mix_width_vals["venue_width"]), minwidth=tkfont.Font().measure("Venue"), stretch=1)
        self.mix_list.column("created", width=max(self.mix_width_vals["created_width"]), minwidth=tkfont.Font().measure("Created"), stretch=1)
        self.mix_list.column("updated", width=max(self.mix_width_vals["updated_width"]), minwidth=tkfont.Font().measure("Updated"), stretch=1)




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
                
            # This Query exists to check, if a window is already open. If yes,
            # then it just focuses. Or it closes and opens up again with the current mix data.

            if self.mix_edit_win.win_state != "normal": 
                self.mix_edit_win = edit_mix_view(self.main_win, mix) 

            elif self.mix_edit_win.win_state == "normal" and cur_sel_mix is cur_sel_mix: 
                log.debug("GUI: Focused Mix Edit Window") 
                self.mix_edit_win.edit_win.focus()

            elif self.mix_edit_win.win_state == "normal" and cur_sel_mix is not cur_sel_mix:
                log.debug("GUI: Reloaded Mix Edit Window") 
                self.mix_edit_win._quit()

                self.mix_edit_win = edit_mix_view(self.main_win, mix)
                self.mix_edit_win.edit_win.focus()

            log.debug("GUI: Mix Window State is " + self.mix_edit_win.win_state)


            

        
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
            
            self.add_mix_win.edit_win.protocol("WM_DELETE_WINDOW", self.update_mix_list)
        
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
            
            
            self.track_edit_win.edit_win.protocol("WM_DELETE_WINDOW", self.update_track_list)


####################################################################
    ########## DELETE MIX ##########################################

    def delete_mix(self):
        cur_mix = self.mix_list.focus()
        mix = models.Mix(self.conn, self.mix_list.item(cur_mix,"text"))
        try:
            mix.delete()
            log.info("GUI: Deleted Mix from list")
            self.status.set("Deleted Mix!")
        except:
            log.error("GUI; Failed to delete Mix!")
            self.status.set("Failed to delete Mix!")

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

    def create_widgets(self):

        self.mix_frame = tk.LabelFrame(self.main_win, text="Mixes")
        self.tracks_frame = tk.LabelFrame(self.main_win, text="Tracks in Mix")

        ########################################################################

        # MIXES LISTVIEW

        self.mix_list = ttk.Treeview(self.mix_frame)
        self.mix_list.pack(fill="both", expand=1)
        self.mix_list['show'] = 'headings'

        self.mix_list["columns"]=("mix_id_col", "name", "played", "venue", "created", "updated")
        self.mix_list.column("mix_id_col", width=2, stretch=1)
        self.mix_list.column("name", width=2, stretch=1)
        self.mix_list.column("played", width=2, stretch=1)
        self.mix_list.column("venue", width=2, stretch=1)
        self.mix_list.column("created", width=2, stretch=1)
        self.mix_list.column("updated", width=2, stretch=1)

        self.mix_list.heading("mix_id_col",text="Mix #", anchor=tk.W, command=lambda _col="mix_id_col": self.treeview_sort_column(self.mix_list, _col, False))
        self.mix_list.heading("name", text="Name", anchor=tk.W, command=lambda _col="name": self.treeview_sort_column(self.mix_list, _col, False))
        self.mix_list.heading("played", text="Played",anchor=tk.W, command=lambda _col="played": self.treeview_sort_column(self.mix_list, _col, False))
        self.mix_list.heading("venue", text="Venue",anchor=tk.W, command=lambda _col="venue": self.treeview_sort_column(self.mix_list, _col, False))
        self.mix_list.heading("created", text="Created",anchor=tk.W, command=lambda _col="created": self.treeview_sort_column(self.mix_list, _col, False))
        self.mix_list.heading("updated", text="Updated",anchor=tk.W, command=lambda _col="updated": self.treeview_sort_column(self.mix_list, _col, False))


        # TRACKS LISTVIEW

        self.tracks_list = ttk.Treeview(self.tracks_frame)
        self.tracks_list.pack(fill="both", expand=1)
        self.tracks_list['show'] = 'headings'

        self.tracks_list["columns"]=("track_pos", "artist", "track", "key", "bpm", "keynotes", "transr", "transnotes", "notes", "d_release_id")
        self.tracks_list.column("track_pos", width=2)
        self.tracks_list.column("artist", width=2)
        self.tracks_list.column("track", width=2)
        self.tracks_list.column("key", width=2) 
        self.tracks_list.column("bpm", width=2)
        self.tracks_list.column("keynotes", width=2) 
        self.tracks_list.column("transr", width=2)
        self.tracks_list.column("transnotes", width=2)
        self.tracks_list.column("notes", width=2)
        self.tracks_list.column("d_release_id", width=2)


        self.tracks_list.heading("track_pos", text="#",anchor=tk.W)
        self.tracks_list.heading("artist", text="Artist", anchor=tk.W)
        self.tracks_list.heading("track", text="Track Name",anchor=tk.W)
        self.tracks_list.heading("key", text="Key",anchor=tk.W)
        self.tracks_list.heading("bpm", text="BPM",anchor=tk.W)
        self.tracks_list.heading("keynotes", text="Key Notes",anchor=tk.W)
        self.tracks_list.heading("transr", text="Trans. Rating",anchor=tk.W)
        self.tracks_list.heading("transnotes", text="Trans. Notes",anchor=tk.W)
        self.tracks_list.heading("notes", text="Notes",anchor=tk.W)
        self.tracks_list.heading("d_release_id", text="Mix Track ID",anchor=tk.W) 

        #########################################################################

        # STATUS BAR

        self.status=tk.StringVar()  
        self.status_bar = tk.Label(self.main_win, textvariable=self.status, anchor=tk.W, bd=1, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, anchor="s", fill=tk.X, expand=tk.YES)

        self.status.set("Ready...")

        #########################################################################
        # BUTTON AREA
        #########################################################################

        self.btn_frame = tk.Frame(self.main_win)
        
        self.new_mix_btn = tk.Button(self.btn_frame, text="New Mix", command=lambda: self.open_widget("add_mix"))
        self.edit_mix_btn = tk.Button(self.btn_frame, text="Edit Mix", command=lambda: self.open_widget("edit_mix"))
        self.del_mix_btn = tk.Button(self.btn_frame, text="Delete Mix", command=self.delete_mix)
        self.edit_track_btn = tk.Button(self.btn_frame, text="Edit Track Info", command=lambda: self.open_widget("track_edit"))
        self.rmv_track_btn = tk.Button(self.btn_frame, text="Remove Track")
        

        self.new_mix_btn.pack(side="left")
        self.edit_mix_btn.pack(side="left")
        self.del_mix_btn.pack(side="left")
        self.edit_track_btn.pack(side="right")
        self.rmv_track_btn.pack(side="right")
        
        

        self.btn_frame.pack(side="bottom", fill="x", expand=1, padx=5)

        # Display Both Lists

        self.mix_frame.pack(fill="both", expand=1, side = "top")
        self.tracks_frame.pack(fill="both", expand=1, side = "bottom")


        


main_gui = main_frame()
main_gui.main_win.mainloop()
        
    

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
from tabulate import tabulate as tab


#################################

class main_frame():
    def __init__(self):


        self.main_win = tk.Tk()                           
        self.main_win.geometry("800x600")                # Fixed size for now, maybe scalable later
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
        # SETUP / INIT

        self.db_obj = models.Database(db_file = self.discobase)
        #Debugging DB Connection

        try:
            self.conn = self.db_obj.db_conn
            log.info("GUI: DB Connection Success")
            self.status.set("DB Connection Success")
        except:
            log.error("GUI: DB connection failed")
            self.status.set("DB Connection failed")

        self.all_mix = models.Mix(self.conn, "all")
        self.mixes_data = self.all_mix.get_all_mixes()

        #################################################
        # TODO: Make column widths as wide as the widest dataset of each column



        # To set the qidth of every column correctly, we have to get all the
        # values that will be inserted first and get the highest one

        # Thus, we start by creating an empty dictionary and adding all the values to it

        mix_width_vals = {}     
        mix_width_vals["mix_id_width"] = []
        mix_width_vals["name_width"] = []
        mix_width_vals["played_width"] = []
        mix_width_vals["venue_width"] = []
        mix_width_vals["created_width"] = []
        mix_width_vals["updated_width"] = []

        for i, row in enumerate(self.mixes_data):
            try:
                # Here, the "text"-value is also set with the mix-id, so we can fetch it 
                # later when we get the tracklist
                # The "text"-column is not shown, it serves just as ID
                self.mix_list.insert("" , i, text=row["mix_id"], values=(row["mix_id"], row["name"], row["played"], row["venue"], row["created"], row["updated"]))
                
                # Append the Char_length widths to the Dictionary.
                # If they are zero or unreadable, append a default value.
                # CURRENTLY: Mix Id returns Nothing for some reason
                #FIXME
                try:
                    mix_width_vals["mix_id_width"].append(len(row["mix_id"]))
                except:
                    mix_width_vals["mix_id_width"].append(3)
                    # log.error("GUI: Mix ID width not fetched. Set default value 3.")
                try:
                    mix_width_vals["name_width"].append(len(row["name"]))
                except:
                    log.error("GUI: Name width not fetched.")
                    mix_width_vals["name_width"].append(3)
                try:
                    mix_width_vals["played_width"].append(len(row["played"]))
                except:
                    mix_width_vals["played_width"].append(3)
                    log.error("GUI: Played width not fetched. Set default value 3.")
                try:
                    mix_width_vals["venue_width"].append(len(row["venue"]))
                except:
                    mix_width_vals["venue_width"].append(3)
                    log.error("GUI: Venue width not fetched.")
                try:
                    mix_width_vals["created_width"].append(len(row["created"]))
                except:
                    mix_width_vals["created_width"].append(3)
                    log.error("GUI: created width not fetched.")
                try:
                    mix_width_vals["updated_width"].append(len(row["updated"]))
                except:
                    mix_width_vals["updated_width"].append(3)
                    log.error("GUI: Updated width not fetched.")


                log.debug("GUI: Inserted Mix Row")
                self.status.set("Inserted Mix Row")

            except:
                log.error("GUI: Inserting Mix Row failed")
                self.status.set("Inserting Mix Row failed")


        self.mix_list.column("mix_id_col", width=max(mix_width_vals["mix_id_width"])*10)
        self.mix_list.column("name", width=max(mix_width_vals["mix_id_width"])*40)
        # print(max(mix_width_vals["mix_id_width"]))
        self.mix_list.column("played", width=max(mix_width_vals["played_width"])*7)
        self.mix_list.column("venue", width=max(mix_width_vals["venue_width"])*7)
        self.mix_list.column("created", width=max(mix_width_vals["created_width"])*7)
        self.mix_list.column("updated", width=max(mix_width_vals["updated_width"])*7)

        

        self.mix_list.bind('<<TreeviewSelect>>', self.show_mix)

        
        self.focus_first_object()
        
    
    def show_mix(self, event):
        # This function gets called, when the user selects a mix in the List of Mixes
        # Here we fetch the selected Mix in the Mix Treeview 
        curItem = self.mix_list.focus()
        try:
            mix = models.Mix(self.conn, self.mix_list.item(curItem,"text"))
            print(self.mix_list.item(curItem,"text"))
            
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
        
        


        if mix_data is not []:
            
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
                # print('Pos: {}, Track: {}'.format(row['track_pos'], row['d_track_name']))
                try:
                    self.tracks_list.insert("", i, text="" , values=(row["track_pos"], row[""], row["d_track_name"], row["key"], row["bpm"], row["key_notes"], row["trans_rating"], row["trans_notes"], row["notes"]))
                   # And here we check the dictionary for the biggest width value
                    try:
                        track_width_vals["track_pos_width"].append(len(row["track_pos"]))
                    except:
                        track_width_vals["track_pos_width"].append(3)
                        log.error("GUI: Track Position width not fetched. Set default value 3.")

                    try:
                        track_width_vals["d_artist_width"].append(len(row["d_artist"]))
                        print(row["d_artist_width"])
                    except:
                        log.error("GUI: Artist width not fetched.")
                        track_width_vals["d_artist_width"].append(3)
                        log.error("GUI: Artist width not fetched. Set default value 3.")

                    try:
                        track_width_vals["d_track_name_width"].append(len(row["d_track_name"]))
                    except:
                        track_width_vals["d_track_name_width"].append(3)
                        log.error("GUI: Track Name width not fetched. Set default value 3.")

                    try:
                        track_width_vals["key_width"].append(len(row["key"]))
                    except:
                        track_width_vals["key_width"].append(3)
                        log.error("GUI: Key width not fetched.")

                    try:
                        track_width_vals["bpm_width"].append(len(row["bpm"]))
                    except:
                        track_width_vals["bpm_width"].append(3)
                        log.error("GUI: BPM width not fetched.")

                    try:
                        track_width_vals["key_notes_width"].append(len(row["key_notes"]))
                    except:
                        track_width_vals["key_notes_width"].append(3)
                        log.error("GUI: Key Notes width not fetched.")   

                    try:
                        track_width_vals["trans_rating_width"].append(len(row["trans_rating"]))
                    except:
                        track_width_vals["trans_rating_width"].append(3)
                        log.error("GUI: Trans Rating width not fetched.")   

                    try:
                        track_width_vals["trans_notes_width"].append(len(row["trans_notes"]))
                    except:
                        track_width_vals["trans_notes_width"].append(3)
                        log.error("GUI: Trans Notes width not fetched.")   

                    try:
                        track_width_vals["notes_width"].append(len(row["notes"]))
                    except:
                        track_width_vals["notes_width"].append(3)
                        log.error("GUI: Notes width not fetched.")                  
                    
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


        else:
            log.error(f"GUI: Mix Data is {str(mix_data)}")
            self.status.set(f"GUI: Mix Data is {str(mix_data)}")
            self.tracks_list.delete(*self.tracks_list.get_children())

        #FIXME ValueError: max() arg is an empty sequence @ Track_Pos


        self.tracks_list.column("track_pos", width=max(track_width_vals["track_pos_width"])*10)
        self.tracks_list.column("d_artist", width=max(track_width_vals["d_artist_width"])*40)
        # print(max(track_width_vals["track_id_width"]))
        self.tracks_list.column("d_track_name", width=max(track_width_vals["d_track_name_width"])*7)
        self.tracks_list.column("key", width=max(track_width_vals["key_width"])*7)
        self.tracks_list.column("bpm", width=max(track_width_vals["bpm_width"])*7)
        self.tracks_list.column("key_notes", width=max(track_width_vals["key_notes_width"])*7)
        self.tracks_list.column("trans_rating", width=max(track_width_vals["trans_rating_width"])*7)
        self.tracks_list.column("trans_notes", width=max(track_width_vals["key_notes_width"])*7)
        self.tracks_list.column("notes", width=max(track_width_vals["notes_width"])*7)


    def focus_first_object(self):
        try:
            start_child_id = self.mix_list.get_children()[0]
            self.mix_list.focus(start_child_id)
            self.mix_list.selection_set(start_child_id)

            log.debug("GUI: Set Focus on first Mix Item")

        except:
            log.error("GUI: Couldn't Set Focus on Mix Item")
            self.status.set("Couldn't Set Focus on Mix Item")
        


    def open_widget(self, view):

        # This function gets called, when the user opens up a window.
        # Depending on the Button he presses, the selector chooses wich window will be opened.
        # They are all inherite from the same base-window class.

        if view == "edit_mix":
            curItem = self.mix_list.focus()
            try:
                mix = models.Mix(self.conn, self.mix_list.item(curItem,"text")) 
                mix_data = mix.get_mix_info() 
                log.debug("GUI: Retrieved Mix Info")   
                self.status.set("Retrieved Mix Info") 
                
                # This Query exists to check, if a window is already open. If yes,
                # then it just focuses. Or it closes and opens up again with the current mix data.
                try:
                    if self.mix_edit_win.win_state == "normal" and curItem is self.mix_list.focus(): 
                        log.debug("GUI: Focused Mix Edit Window") 
                        self.mix_edit_win.edit_win.focus()

                    elif self.mix_edit_win.win_state == "normal" and curItem is not self.mix_list.focus():
                        log.debug("GUI: Reloaded Mix Edit Window") 
                        self.mix_edit_win._quit()

                        try:
                            mix = models.Mix(self.conn, self.mix_list.item(self.mix_list.focus(),"text"))
                            mix_data = mix.get_mix_info() 
                            log.debug("GUI: Got Mix data again") 

                        except:
                            log.error("GUI: Couldn't get mix data again")

                        self.mix_edit_win = edit_mix_view(self.main_win, mix_data, self.conn)
                        self.mix_edit_win.edit_win.focus()

                    log.debug("GUI: Mix Window State is " + self.mix_edit_win.win_state)

                except:
                    self.mix_edit_win = edit_mix_view(self.main_win, mix_data, self.conn)  
                    log.debug("GUI: Mix Window State is " + self.mix_edit_win.win_state) 

            except: 
                log.error("GUI: Getting Mix Data failed")
                self.status.set("Getting Mix Data failed")  

        
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

            
        elif view == "track_edit":

            curItem = self.tracks_list.focus()
            try:
                track = models.Mix(self.conn, self.tracks_list.item(curItem,"track_pos")) 
                track_data = track.get_one_mix_track() 
                log.debug("GUI: Retrieved Track Info")   
                self.status.set("Retrieved Track Info") 
                
                # ############## # # # # # # # # # #
                try:
                    if self.track_edit_win.win_state == "normal" and curItem is self.tracks_list.focus(): 
                        log.debug("GUI: Focused Track Edit Window") 
                        self.track_edit_win.edit_win.focus()

                    elif self.track_edit_win.win_state == "normal" and curItem is not self.track_list.focus():
                        log.debug("GUI: Reloaded Track Edit Window") 
                        self.track_edit_win._quit()

                        try:
                            track = models.Mix(self.conn, self.tracks_list.item(self.mix_list.focus(),"text")) # # START HERE

                        # Fetch Mix data with Mix ID
                        # THEN fetch get_one_mix with track Id
                        # what is track_id?

                            track_data = track.get_one_mix_track() 
                            log.debug("GUI: Got Track data again") 

                        except:
                            log.error("GUI: Couldn't get Track data again")

                        self.track_edit_win = edit_track_info(self.main_win, track_data, self.conn)
                        self.track_edit_win.edit_win.focus()

                    log.debug("GUI: Track Window State is " + self.track_edit_win.win_state)

                except:
                    self.track_edit_win = edit_track_info(self.main_win, track_data, self.conn)  
                    log.debug("GUI: Track Window State is " + self.track_edit_win.win_state) 

            except: 
                log.error(f"GUI: Getting Track Data failed. Position: {self.tracks_list.item(curItem)}")
                self.status.set("Getting Track Data failed")  


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
        self.mix_list.column("mix_id_col", width=2, stretch=0)
        self.mix_list.column("name", width=2, stretch=0)
        self.mix_list.column("played", width=2, stretch=0)
        self.mix_list.column("venue", width=2, stretch=0)
        self.mix_list.column("created", width=2, stretch=0)
        self.mix_list.column("updated", width=2, stretch=0)

        self.mix_list.heading("mix_id_col",text="Mix #",anchor=tk.W)
        self.mix_list.heading("name", text="Name", anchor=tk.W)
        self.mix_list.heading("played", text="Played",anchor=tk.W)
        self.mix_list.heading("venue", text="Venue",anchor=tk.W)
        self.mix_list.heading("created", text="Created",anchor=tk.W)
        self.mix_list.heading("updated", text="Updated",anchor=tk.W)


        # TRACKS LISTVIEW

        self.tracks_list = ttk.Treeview(self.tracks_frame)
        self.tracks_list.pack(fill="both", expand=1)
        self.tracks_list['show'] = 'headings'

        self.tracks_list["columns"]=("track_pos", "artist", "track", "key", "bpm", "keynotes", "transr", "transnotes", "d_release_id")
        self.tracks_list.column("track_pos", width=2)
        self.tracks_list.column("artist", width=2)
        self.tracks_list.column("track", width=2)
        self.tracks_list.column("key", width=2) 
        self.tracks_list.column("bpm", width=2)
        self.tracks_list.column("keynotes", width=2) 
        self.tracks_list.column("transr", width=2)
        self.tracks_list.column("transnotes", width=2)
        self.tracks_list.column("d_release_id", width=2)


        self.tracks_list.heading("track_pos", text="Track Pos",anchor=tk.W)
        self.tracks_list.heading("artist", text="Artist", anchor=tk.W)
        self.tracks_list.heading("track", text="Track Name",anchor=tk.W)
        self.tracks_list.heading("key", text="Key",anchor=tk.W)
        self.tracks_list.heading("bpm", text="BPM",anchor=tk.W)
        self.tracks_list.heading("keynotes", text="Key Notes",anchor=tk.W)
        self.tracks_list.heading("transr", text="Trans. Rating",anchor=tk.W)
        self.tracks_list.heading("transnotes", text="Trans. Notes",anchor=tk.W)
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
        self.del_mix_btn = tk.Button(self.btn_frame, text="Delete Mix")
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
        
    

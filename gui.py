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

        # Create Dictionary for all columns
        # Dictionary["name"] = []

        for i, row in enumerate(self.mixes_data):
            try:
                # self.mix_list.column('name', width=len(row["name"]))
                # print(len(row["name"]))
                # Append all width numbers to the list per dictionary entry

                self.mix_list.insert("" , i, text=row["mix_id"], values=(row["name"], row["played"], row["venue"], row["created"], row["updated"]))
                log.debug("GUI: Inserted Mix Row")
                self.status.set("Inserted Mix Row")
            except:
                log.error("GUI: Inserting Mix Row failed")
                self.status.set("Inserting Mix Row failed")

            

        # Get the highest number of every column-dataset of the dictionary
        # set every columnwdith equal to the highest number

        self.mix_list.bind('<<TreeviewSelect>>', self.show_mix)

        try:
            start_child_id = self.mix_list.get_children()[0]
            self.mix_list.selection_set(start_child_id)
            log.debug("GUI: Set Focus on first Mix Item")

        except:
            log.error("GUI: Couldn't Set Focus on Mix Item")
            self.status.set("Couldn't Set Focus on Mix Item")

        

    
    def show_mix(self, event):

        curItem = self.mix_list.focus()

        
            

        try:
            mix = models.Mix(self.conn, self.mix_list.item(curItem,"text"))
            mix_data = mix.get_full_mix(verbose = True) 
            log.debug("GUI: Retrieved Mix data")   
            self.status.set("Retrieved Mix data") 

        except: 
            log.error("GUI: Getting Mix Data failed")
            self.status.set("Getting Mix Data failed")  
        
        
        ########################################################

        if mix_data is not []:
            
            self.tracks_list.delete(*self.tracks_list.get_children())
            for i, row in enumerate(mix_data):
                try:
                    self.tracks_list.insert("", i, text=row["d_artist"] , values=(row["d_track_name"], row["d_track_no"], row["key"], row["bpm"], row["key_notes"], row["trans_rating"], row["trans_notes"], row["notes"]))
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
        


    def open_widget(self, view):

        if view == "edit_mix":
            curItem = self.mix_list.focus()
            try:
                mix = models.Mix(self.conn, self.mix_list.item(curItem,"text")) 
                mix_data = mix.get_mix_info() 
                log.debug("GUI: Retrieved Mix Info")   
                self.status.set("Retrieved Mix Info") 
                
                # ############## # # # # # # # # # #
                # TODO: Get Mix Edit Window to change info on selected list item in mix view
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
                track = models.Mix(self.conn, self.tracks_list.item(curItem,"d_release_id")) 
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
                log.error("GUI: Getting Track Data failed")
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

        self.mix_list["columns"]=("name","played", "venue", "created", "updated")
        self.mix_list.column("#0", width=20,  minwidth=4)
        self.mix_list.column("name", width=80, minwidth=80)
        self.mix_list.column("played", width=20,  minwidth=20)
        self.mix_list.column("venue", width=80, minwidth=25)
        self.mix_list.column("created", width=80, minwidth=20)
        self.mix_list.column("updated", width=80, minwidth=20)

        self.mix_list.heading("#0",text="Mix #",anchor=tk.W)
        self.mix_list.heading("name", text="Name", anchor=tk.W)
        self.mix_list.heading("played", text="Played",anchor=tk.W)
        self.mix_list.heading("venue", text="Venue",anchor=tk.W)
        self.mix_list.heading("created", text="Created",anchor=tk.W)
        self.mix_list.heading("updated", text="Updated",anchor=tk.W)


        # TRACKS LISTVIEW

        self.tracks_list = ttk.Treeview(self.tracks_frame)
        self.tracks_list.pack(fill="both", expand=1)

        self.tracks_list["columns"]=("artist", "track", "trackpos", "key", "bpm", "keynotes", "transr", "transnotes", "d_release_id")
        self.tracks_list.column("#0", width=20,  minwidth=10)
        self.tracks_list.column("artist", width=20, minwidth=10)
        self.tracks_list.column("track", width=20,  minwidth=10)
        self.tracks_list.column("trackpos", width=10, minwidth=10)
        self.tracks_list.column("key", width=8, minwidth=8)
        self.tracks_list.column("bpm", width=8, minwidth=8)
        self.tracks_list.column("keynotes", width=10, minwidth=5)
        self.tracks_list.column("transr", width=10, minwidth=5)
        self.tracks_list.column("transnotes", width=10, minwidth=5)
        self.tracks_list.column("d_release_id", width=20, minwidth=10)


        self.tracks_list.heading("#0", text="Artist", anchor=tk.W)
        self.tracks_list.heading("track", text="Track Name",anchor=tk.W)
        self.tracks_list.heading("trackpos", text="Track Pos",anchor=tk.W)
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
        
    

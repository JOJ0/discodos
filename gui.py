################################
# IMPORTS

from discodos import views
from discodos import ctrls
from discodos import models
from discodos import utils
from discodos import log
from discodos.widgets import edit_mix_view
from discodos.widgets import edit_track_info
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tabulate import tabulate as tab


#################################

class main_frame():
    def __init__(self):

        self.mix_window_started = False
        self.track_window_started = False

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
            log.info("DB Connection Success")
            self.status.set("DB Connection Success")
        except:
            log.error("DB connection failed")
            self.status.set("DB Connection failed")

        self.all_mix = models.Mix(self.conn, "all")
        self.mixes_data = self.all_mix.get_all_mixes()

        for i, row in enumerate(self.mixes_data):
            try:
                self.mix_list.insert("" , i, text=row["mix_id"], values=(row["name"], row["played"], row["venue"], row["created"], row["updated"]))
                log.debug("Inserted Mix Row")
                self.status.set("Inserted Mix Row")
            except:
                log.error("Inserting Mix Row failed")
                self.status.set("Inserting Mix Row failed")

        self.mix_list.bind('<<TreeviewSelect>>', self.show_mix)

        try:
            start_child_id = self.mix_list.get_children()[0]
            self.mix_list.selection_set(start_child_id)
            log.debug("Set Focus on first Item")
        except:
            log.debug("Couldn't Set Focus on First Item")
            self.status.set("Couldn't Set Focus on First Item")

    
    def show_mix(self, event):

        curItem = self.mix_list.focus()
        try:
            mix = models.Mix(self.conn, self.mix_list.item(curItem,"text"))
            mix_data = mix.get_full_mix(verbose = True) 
            log.debug("Retrieved Mix data")   
            self.status.set("Retrieved Mix data")   
        except: 
            log.error("Getting Mix Data failed")
            self.status.set("Getting Mix Data failed")  

            # TODO
            # Everything's working except RELEASE

        if mix_data is not False:
            for i, row in enumerate(mix_data):
                try:
                    self.tracks_list.insert("" , i, text="", values=(row["d_artist"], row["d_track_name"], row["d_track_no"], row["key"], row["bpm"], row["key_notes"], row["trans_rating"], row["trans_notes"], row["notes"]))
                    log.info("Inserted Track row")
                    self.status.set("Inserted Track row")  
                except:
                    log.error("Inserting Track Row failed")
                    self.status.set("Inserting Track Row failed") 
        else:
            log.error("Mix Data is " + str(mix_data))
            self.status.set("Mix Data is " + str(mix_data)) 
            self.tracks_list.delete(*self.tracks_list.get_children())


    def open_widget(self, view):
        if view == "mix" and not self.mix_window_started:
            curItem = self.mix_list.focus()
            try:
                mix = models.Mix(self.conn, self.mix_list.item(curItem,"text"))
                mix_data = mix.get_mix_info() 
                log.debug("Retrieved Mix Info")   
                self.status.set("Retrieved Mix Info") 
                self.mix_edit_win = edit_mix_view(self.main_win, mix_data)  
                self.mix_window_started = True
            except: 
                log.error("Getting Mix Data failed")
                self.status.set("Getting Mix Data failed")  
            

        elif view == "track":
            self.track_edit_win = edit_track_info(self.main_win)




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

        self.tracks_list["columns"]=("artist", "track", "trackpos", "key", "bpm", "keynotes", "transr", "transnotes", "tracknotes")
        self.tracks_list.column("#0", width=20,  minwidth=10)
        self.tracks_list.column("artist", width=20, minwidth=10)
        self.tracks_list.column("track", width=20,  minwidth=10)
        self.tracks_list.column("trackpos", width=10, minwidth=10)
        self.tracks_list.column("key", width=8, minwidth=8)
        self.tracks_list.column("bpm", width=8, minwidth=8)
        self.tracks_list.column("keynotes", width=10, minwidth=5)
        self.tracks_list.column("transr", width=10, minwidth=5)
        self.tracks_list.column("transnotes", width=10, minwidth=5)
        self.tracks_list.column("tracknotes", width=20, minwidth=10)


        self.tracks_list.heading("#0",text="Release",anchor=tk.W)
        self.tracks_list.heading("artist", text="Artist", anchor=tk.W)
        self.tracks_list.heading("track", text="Track Name",anchor=tk.W)
        self.tracks_list.heading("trackpos", text="Track Pos",anchor=tk.W)
        self.tracks_list.heading("key", text="Key",anchor=tk.W)
        self.tracks_list.heading("bpm", text="BPM",anchor=tk.W)
        self.tracks_list.heading("keynotes", text="Key Notes",anchor=tk.W)
        self.tracks_list.heading("transr", text="Trans. Rating",anchor=tk.W)
        self.tracks_list.heading("transnotes", text="Trans. Notes",anchor=tk.W)
        self.tracks_list.heading("tracknotes", text="Track Notes",anchor=tk.W)

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
        
        self.new_mix_btn = tk.Button(self.btn_frame, text="New Mix")
        self.edit_mix_btn = tk.Button(self.btn_frame, text="Edit Mix", command=lambda: self.open_widget("mix"))
        self.del_mix_btn = tk.Button(self.btn_frame, text="Delete Mix")
        self.edit_track_btn = tk.Button(self.btn_frame, text="Edit Track Info", command=lambda: self.open_widget("track"))
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
        
    

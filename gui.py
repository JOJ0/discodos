################################
# IMPORTS

from discodos import views
from discodos import ctrls
from discodos import models
from discodos import utils
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
            print("DB Connection Success")
        except:
            print("DB connection failed")

        self.all_mix = models.Mix(self.conn, "all")
        self.mixes_data = self.all_mix.get_all_mixes()

        for i, row in enumerate(self.mixes_data):
            self.mix_list.insert("" , i, text=row["mix_id"], values=(row["name"], row["played"], row["venue"], row["created"], row["updated"]))

        self.mix_list.bind('<<TreeviewSelect>>', self.show_mix)

    
    def show_mix(self, event):
        mix = models.Mix(self.conn, self.mix_list.selection()[0])
        print(mix)

        
        # item = self.mix_list.selection()[0]
        # print("you clicked on", self.mix_list.item(item,"text"))




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

        self.tracks_list["columns"]=("name","played", "venue", "created", "updated")
        self.tracks_list.column("#0", width=20,  minwidth=4)
        self.tracks_list.column("name", width=80, minwidth=80)
        self.tracks_list.column("played", width=20,  minwidth=20)
        self.tracks_list.column("venue", width=80, minwidth=25)
        self.tracks_list.column("created", width=80, minwidth=20)
        self.tracks_list.column("updated", width=80, minwidth=20)

        self.tracks_list.heading("#0",text="Mix #",anchor=tk.W)
        self.tracks_list.heading("name", text="Name", anchor=tk.W)
        self.tracks_list.heading("played", text="Played",anchor=tk.W)
        self.tracks_list.heading("venue", text="Venue",anchor=tk.W)
        self.tracks_list.heading("created", text="Created",anchor=tk.W)
        self.tracks_list.heading("updated", text="Updated",anchor=tk.W)

        #########################################################################

        # Display Both Lists

        self.mix_frame.pack(fill="both", expand=1, side = "top")
        self.tracks_frame.pack(fill="both", expand=1, side = "bottom")


main_gui = main_frame()
main_gui.main_win.mainloop()
        
    

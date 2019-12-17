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
        self.main_win.geometry("800x400")                # Fixed size for now, maybe scalable later
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

    # DISCOGS API config
    def mix_starter(self):
        discodos_root = Path(os.path.dirname(os.path.abspath(__file__)))
        # conf = utils.read_yaml(discodos_root / "config.yaml")
        discobase = discodos_root / "discobase.db"
        # SETUP / INIT

        db_obj = models.Database(db_file = discobase)
        #Debugging DB Connection
        try:
            self.conn = db_obj.db_conn
            print("DB Connection Success")
        except:
            print("DB connection failed")

        self.mix = models.Mix(self.conn, "all")
        self.mixes_data = self.mix.get_all_mixes()

        for i, row in enumerate(self.mixes_data):
            self.mix_list.insert("" , i, text=row["mix_id"], values=(row["name"], row["played"], row["venue"], row["created"], row["updated"]))


    #####################################################################################    
    # CREATE WIDGETS

    def create_widgets(self):
        self.mix_list = ttk.Treeview(self.main_win)
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


main_gui = main_frame()
main_gui.main_win.mainloop()
        
    

from . import views
from . import ctrls
from . import models
import tkinter as tk
from tkinter import ttk

class main_frame():
    def __init__(self):
        self.main_win = tk.Tk()                           
        self.main_win.geometry("860x500")                # Fixed size for now, maybe scalable later
        self.main_win.resizable(False, False)    
        
    
        self.main_win.title("Language Construction Tool") # EDIT: Add relevant Information to title, like Titles in Mix etc

        # Create all Widgets, outsourced to its own function
        self.create_widgets()
        
        
                    
    # Exit GUI cleanly
    def _quit(self):
        self.main_win.quit()
        self.main_win.destroy()
        exit() 

    # Instantiate the DB-Connector and load the Data

    # DISCOGS API config
    def mix_starter(self):
        discodos_root = Path(os.path.dirname(os.path.abspath(__file__)))
        conf = read_yaml(discodos_root / "config.yaml")
        discobase = discodos_root / "discobase.db"
        # SETUP / INIT
        # DEBUG stuff
        #log.info("dir(args): %s", dir(args))
        # check cli args and set attributes
        # also here refactoring is not through - conn should not be needed in future
        # Objects derived from models.py should handle it themselves
        # workaround for now:
        db_obj = Database(db_file = discobase)
        conn = db_obj.db_conn
  
  # Need to find offline mode to pull the data out of the db and insert in list


    #####################################################################################    
    # CREATE WIDGETS

    def create_widgets(self):
        self.mix_list = ttk.Treeview(self.main_win )
        self.mix_list.grid(row=0, column=0, sticky="ns")

        self.mix_list["columns"]=("name","played", "venue", "created", "updated")
        self.mix_list.column("#0",  minwidth=4, stretch=tk.NO)
        self.mix_list.column("name", minwidth=80)
        self.mix_list.column("played",  minwidth=20, stretch=tk.NO)
        self.mix_list.column("venue", width=80, minwidth=25, stretch=tk.NO)
        self.mix_list.column("created", width=80, minwidth=20, stretch=tk.NO)
        self.mix_list.column("updated", width=80, minwidth=20, stretch=tk.NO)

        self.mix_list.heading("#0",text="Mix #",anchor=tk.W)
        self.mix_list.heading("name", text="Name", anchor=tk.W)
        self.mix_list.heading("played", text="Played",anchor=tk.W)
        self.mix_list.heading("venue", text="Venue",anchor=tk.W)
        self.mix_list.heading("created", text="Created",anchor=tk.W)
        self.mix_list.heading("updated", text="Updated",anchor=tk.W)

        mix_ctrl = ctrls.Mix_ctrl_gui()
        print(mix_list.view_mixes_list())
    

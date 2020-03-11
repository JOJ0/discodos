#!/usr/bin/env python
from discodos.gui_views import main_frame
from discodos import utils
from discodos import models
from discodos.gui_ctrls import mix_ctrl_gui
import os
from pathlib import Path
from discodos import log
import tkinter as tk


##################################
# ###### PREPARING INSTANTIATION
        
discodos_root = Path(os.path.dirname(os.path.abspath(__file__)))
# conf = utils.read_yaml(discodos_root / "config.yaml")
discobase = discodos_root / "discobase.db"
# CONFIGURATOR INIT: db and config file handling, DISCOGS API conf
conf = utils.Config()

db_obj = models.Database(db_file = conf.discobase)

##### DB CONN ########################

try:
    conn = db_obj.db_conn
    log.info("GUI: DB Connection Success")
except:
    log.error("GUI: DB Connection Failed")


if __name__ == '__main__':
    root = tk.Tk()  # TKINTER OBJECT
    app = mix_ctrl_gui(root, conn, start_up=True) # GUI CONTROLLER
    root.mainloop() # START WINDOW
        

    

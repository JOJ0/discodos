from discodos.gui_views import main_frame
from discodos import utils
from discodos import models
import os
from pathlib import Path
from discodos import log

# discodos_root = Path(os.path.dirname(os.path.abspath(__file__)))
# print(discodos_root)

######################################## PREPARING INSTANTIATION
        
discodos_root = Path(os.path.dirname(os.path.abspath(__file__)))
# conf = utils.read_yaml(discodos_root / "config.yaml")
discobase = discodos_root / "discobase.db"
# CONFIGURATOR INIT: db and config file handling, DISCOGS API conf
conf = utils.Config()

db_obj = models.Database(db_file = conf.discobase)

################################################## DB CONN

try:
    conn = db_obj.db_conn
    log.info("GUI: DB Connection Success")
except:
    log.error("GUI: DB Connection Failed")


main_gui = main_frame(conn)
main_gui.main_win.mainloop()
        

    

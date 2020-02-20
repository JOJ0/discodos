from discodos.gui_views import setup_frame
from discodos import models
from discodos import utils
import os
from pathlib import Path
from discodos import log


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



setup_gui = setup_frame(conn)
setup_gui.setup_win.mainloop()
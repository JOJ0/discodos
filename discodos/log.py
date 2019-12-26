import logging
from pathlib import Path
import os

def logger_init():
    discodos_lib = Path(os.path.dirname(os.path.abspath(__file__)))
    debug_log = discodos_lib.parents[0] / "debug.log"
    log = logging.getLogger('discodos')
    log.setLevel(logging.DEBUG) # level of logger itself
    f_handle = logging.FileHandler(debug_log) # create file handler
    f_handle.setLevel(logging.DEBUG) # which logs even debug messages
    c_handle = logging.StreamHandler() # console handler with a higher log level
    c_handle.setLevel(logging.WARNING) # level of the console handler
    # create formatters and add it to the handlers
    f_form = logging.Formatter('%(asctime)s %(name)-8s %(levelname)-7s %(message)s',
             datefmt='%Y-%m-%d %H:%M:%S')
    c_form = logging.Formatter('%(levelname)-5s %(message)s')
    c_handle.setFormatter(c_form)
    f_handle.setFormatter(f_form)
    log.addHandler(c_handle) # add the handlers to logger
    log.addHandler(f_handle)
    return log

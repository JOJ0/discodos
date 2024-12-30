import logging
import os
import sys
from pathlib import Path

from discodos.config import create_data_dir


def logger_init():
    # logger is not relying on Config class and handles paths itself
    if getattr(sys, 'frozen', False):
        discodos_root = Path(os.path.dirname(sys.executable))
        discodos_data = create_data_dir(discodos_root)
    else:
    #    discodos_lib = Path(os.path.dirname(os.path.abspath(__file__)))
    #    discodos_root = discodos_lib.parents[0]
    #debug_log = discodos_root / "debug.log"
        discodos_root = Path(os.path.dirname(os.path.abspath(__file__)))
        discodos_data = create_data_dir(discodos_root)
    debug_log = discodos_data / "debug.log"

    log = logging.getLogger('discodos')
    log.setLevel(logging.DEBUG) # level of logger itself
    f_handle = logging.FileHandler(debug_log, encoding='utf-8') # create file handler
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

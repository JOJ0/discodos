#/usr/bin/env python3

import logging

def logger_init():
#    logging.basicConfig(filename='uapi.log',level=logging.DEBUG)
    logger=logging.getLogger()
    handler=logging.StreamHandler()
#    formatter=logging.Formatter('%(asctime)s %s(name)-12s $(levelname)-8s %(message)s')
    formatter=logging.Formatter('%(levelname)-5s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    #logger.setLevel(logging.INFO)
    return logger


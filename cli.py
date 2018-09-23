#!/usr/bin/env python3

from discodos import db
import discogs_client
import csv
import time
import datetime
import sys
import argparse
import logging

def logger_init():
#    logging.basicConfig(filename='uapi.log',level=logging.DEBUG)
    logger=logging.getLogger()
    handler=logging.StreamHandler()
#    formatter=logging.Formatter('%(asctime)s %s(name)-12s $(levelname)-8s %(message)s')
    formatter=logging.Formatter('%(levelname)-5s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger

# argparser init
def argparser(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
		"-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help="increases log verbosity for each occurence.")
    parser.add_argument(
		"command",
        help="command.")
    arguments = parser.parse_args(argv[1:])
    # Sets log level to WARN going more verbose for each new -v.
    log.setLevel(max(3 - arguments.verbose_count, 0) * 10) 
    return arguments 

def main():
	# setup / init
    global log
    log=logger_init()
    args = argparser(sys.argv)
    conn = db.create_conn("/Users/jojo/git/discodos/discobase.db")
    # discogs api connection
    userToken = "NcgNaeOXSCgCfBQsaeKhChNXqEQbKaNBQrayltht"
    d = discogs_client.Client("J0J0 Todos Discodos/0.0.1 +http://github.com/JOJ0",
                              user_token=userToken)
    me = d.identity()

    if args.command == "all":
        # show all releases from sqlite
        db.all_releases(conn)
    
    #for r in me.collection_folders[4].releases:
    
    conn.commit()
    conn.close()
    print("DB closed.")

if __name__ == "__main__":
    main()

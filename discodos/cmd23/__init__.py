#!/usr/bin/env python

from discodos.utils import print_help
from discodos.ctrls import Mix_ctrl_cli, Coll_ctrl_cli
from discodos.config import Db_setup, Config
from discodos.cmd23 import helper, import_, mix, search, setup, stats, suggest
import logging
import sys
import textwrap
import click
import pprint


# globals we use for logging, argparser and user interaction object
log = logging.getLogger('discodos')
args = None
user = None



@click.group()
def main_cmd():
    conf = Config()
    log.handlers[0].setLevel(conf.log_level)  # set configured console log lvl
    user = helper.User()
    # log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = Coll_ctrl_cli(
        False, user,
        conf.discogs_token, conf.discogs_appid, conf.discobase,
        conf.musicbrainz_user, conf.musicbrainz_password
    )


# Add commands
main_cmd.add_command(mix.mix_cmd)
main_cmd.add_command(search.search_cmd)
main_cmd.add_command(import_.import_cmd)
main_cmd.add_command(suggest.suggest_cmd)
main_cmd.add_command(stats.stats_cmd)
main_cmd.add_command(setup.setup_cmd)



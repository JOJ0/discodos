#!/usr/bin/env python

from discodos.utils import print_help
from discodos.args_helper import User_int
from discodos.ctrls import Mix_ctrl_cli, Coll_ctrl_cli
from discodos.config import Db_setup, Config
from discodos.cmd23 import import_, mix, search, setup, stats, suggest
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
    print("Main cmd loading.")
    pass


# Add commands
main_cmd.add_command(mix.mix_cmd)
main_cmd.add_command(search.search_cmd)
main_cmd.add_command(import_.import_cmd)
main_cmd.add_command(suggest.suggest_cmd)
main_cmd.add_command(stats.stats_cmd)
main_cmd.add_command(setup.setup_cmd)



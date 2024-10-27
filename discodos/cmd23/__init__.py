#!/usr/bin/env python
from discodos.config import Config
from discodos.cmd23 import (
    helper,
    import_,
    mix,
    search,
    setup,
    stats,
    suggest,
    ls,
)
import logging
import click


# globals we use for logging, argparser and user interaction object
log = logging.getLogger('discodos')
args = None
user = None


@click.group(
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-v", "--verbose", "verbose_count", count=True, default=0,
    help="""increases output verbosity / shows what DiscoDOS is doing under
    the hood (-v is INFO level, -vv is DEBUG level).""")
@click.option(
    "-o", "--offline", "offline_mode", is_flag=True,
    help="""DiscoDOS checks for connectivity to online services
    (Discogs, MusicBrainz, AcousticBrainz) itself. This option
    forces offline mode. A lot of options work in on- and
    offline mode. Some behave differently, depending on connection state.""")
@click.pass_context
def main_cmd(context, verbose_count, offline_mode):
    conf = Config()
    log.handlers[0].setLevel(conf.log_level)  # set configured console log lvl
    context.obj = helper.User(conf, verbose_count, offline_mode)


# Add commands
main_cmd.add_command(mix.mix_cmd)
main_cmd.add_command(search.search_cmd)
main_cmd.add_command(import_.import_cmd)
main_cmd.add_command(suggest.suggest_cmd)
main_cmd.add_command(stats.stats_cmd)
main_cmd.add_command(setup.setup_cmd)
main_cmd.add_command(ls.ls_cmd)

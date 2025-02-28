import logging
import click

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
    sell,
    clean,
    links,
)


# globals we use for logging, argparser and user interaction object
log = logging.getLogger('discodos')


@click.group(
    cls=helper.AbbreviationGroup,
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-v", "--verbose", "verbose_count", count=True, default=0,
    help="""increases output verbosity / shows what DiscoDOS is doing under
    the hood (-v is INFO level, -vv is DEBUG level).""")
@click.option(
    "-o", "--offline", "offline_mode", is_flag=True,
    help="""Enabling this flag prevents DiscoDOS to check for connectivity to
    online services (Discogs, MusicBrainz) and forces offline mode. A lot of
    DiscoDOS' functionality works well in on- and offline mode but might behave
    differently, depending on connection state.""")
@click.option(
    "-t/-x", "--tui/--no-tui", default=None, show_default=True,
    help="""Use a TUI (Textual framework) version if available. Currently only affects
    "dsc ls" command. Overrides "enable_tui" config option.
    """)
@click.option(
    "--db", "db_file", type=str, default=None,
    help="""Override configured DiscoBASE file.""")
@click.pass_context
def main_cmd(context, verbose_count, offline_mode, tui, db_file):
    conf = Config()
    if tui is not None:
        conf.enable_tui = tui
    if db_file is not None:
        conf.discobase = db_file
    log.handlers[0].setLevel(conf.log_level)  # set configured console log lvl
    context.obj = helper.User(conf, verbose_count, offline_mode)


# Add commands
main_cmd.add_command(mix.mix_cmd)
main_cmd.add_command(search.search_cmd)
main_cmd.add_command(import_.import_group)
main_cmd.add_command(suggest.suggest_cmd)
main_cmd.add_command(stats.stats_cmd)
main_cmd.add_command(setup.setup_cmd)
main_cmd.add_command(ls.ls_cmd)
main_cmd.add_command(links.links_cmd)
main_cmd.add_command(sell.sell_cmd)
main_cmd.add_command(clean.clean_group)

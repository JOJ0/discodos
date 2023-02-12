import click
import logging


log = logging.getLogger('discodos')

@click.command(name='setup')
@click.option(
    "--force", "force_upgrade_schema", is_flag=True,
    help='''Force-upgrade the database schema - use with caution!''')
@click.pass_obj
def setup_cmd(helper, force_upgrade_schema):
    """
    Sets up the DiscoBASE and handles database schema upgrades.
    """
    def update_user_interaction_helper(user):
        pass

    user = update_user_interaction_helper(helper)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)

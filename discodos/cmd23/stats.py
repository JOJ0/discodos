import click
import logging


log = logging.getLogger('discodos')

@click.command(name='stats')
@click.pass_obj
def stats_cmd(helper):
    """
    Displays statistics about the collection.

    Besides showing stats like the size of the collection (on Discogs vs. in
    the DiscoBASE) also counts on existing mixes, how many tracks they contain
    and which additional metadata is present, are availalbe.
    """
    def update_user_interaction_helper(user):
        pass

    user = update_user_interaction_helper(helper)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)

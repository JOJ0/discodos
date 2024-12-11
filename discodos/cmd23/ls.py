import logging
import click

from discodos.ctrl import CollectionControlCommandline

log = logging.getLogger('discodos')


@click.command(
    context_settings={
        "ignore_unknown_options": True,
        # allow_extra_args=True,
    },
    name="ls",
)
@click.argument("search_terms", metavar="SEARCH_TERMS", nargs=-1)
@click.option("--order-by", "-o", type=str, help="order by DiscoBASE field")
@click.pass_obj
def ls_cmd(helper, search_terms, order_by):
    """Searches and lists collection items.

    Supports key=value search. Available keys can be either full DiscoBASE field names
    or abbreviations of those: id, listing, artist, title, collection, cat, price,
    status, sold.
    """
    def update_user_interaction_helper(user):
        user.WANTS_ONLINE = True
        user.WANTS_TO_SEARCH_FOR_RELEASE = True
        if not search_terms:
            user.WANTS_TO_LIST_ALL_RELEASES = True
            user.WANTS_TO_SEARCH_FOR_RELEASE = False
        return user

    user = update_user_interaction_helper(helper)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    try:  # Catch when `=` character is missing and assume title column
        search_key_value = dict([
                item.split("=") if "=" in item else ["title", item]
                for item in search_terms
        ])
    except ValueError as error:
        coll_ctrl.cli.p(error)

    if user.WANTS_TO_LIST_ALL_RELEASES:
        coll_ctrl.view_all_releases()
        # maybe put a rich pager here?
        return
    if user.conf.enable_tui:
        coll_ctrl.tui_ls_releases(search_key_value, orderby=order_by)
    else:
        coll_ctrl.ls_releases(search_key_value)

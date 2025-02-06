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
@click.option("--reverse", "-r", is_flag=True, help="reverse order")
@click.option("--limit", "-l", type=int, help="limit results")
@click.option(
    "--all", "--extra", "-a", "-e", "sales_extra", is_flag=True,
    help="""By default sales and collection items are displayed in a 'combined' view.
    That is, listing ID if applicable, is added to collection item's respective column)
    with the caveat that non-collection items can't be viewed that way. Enabling this
    option displays a separate entry for each sales listing/collection item, allowing to
    include sold items that were removed from the collection.
    """,
)
@click.pass_obj
def ls_cmd(helper, search_terms, order_by, reverse, sales_extra, limit):
    """Searches and lists collection items.

    Supports key=value search. Available keys can be either full DiscoBASE field names
    or abbreviations of those: id, listing, artist, title, collection, cat, price,
    status, sold.
    """
    def update_user_interaction_helper(user):
        user.WANTS_ONLINE = True
        user.WANTS_TO_SEARCH_FOR_RELEASE = True
        if not search_terms:
            user.WANTS_TO_SEARCH_FOR_RELEASE = False
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    try:  # Catch when `=` character is missing and assume title column
        search_key_value = coll_ctrl.prepare_key_value_search(query=search_terms)
    except ValueError as error:
        coll_ctrl.cli.p(error)

    if user.conf.enable_tui:
        coll_ctrl.tui_ls_releases(
            search_key_value,
            orderby=order_by,
            reverse_order=reverse,
            sales_extra=sales_extra,
            limit=limit,
        )
    else:
        coll_ctrl.ls_releases(
            search_key_value,
            orderby=order_by,
            reverse_order=reverse,
            sales_extra=sales_extra,
            limit=limit,
        )

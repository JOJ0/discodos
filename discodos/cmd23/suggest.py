import logging
import click

from discodos.ctrl import CollectionControlCommandline

log = logging.getLogger('discodos')


@click.command(name='suggest')
@click.argument('suggest_search', nargs=1, metavar='SEARCH_TERMS', default="0")
@click.option(
    "-b", "--bpm", 'suggest_bpm', type=int, metavar="BPM",
    help='''suggests tracks based on BPM value, within a
    pitch-range of +/-6 percent.''')
@click.option(
    "-k", "--key", 'suggest_key', type=str, metavar="KEY",
    help='suggests tracks based on musical key.')
@click.pass_obj
def suggest_cmd(helper, suggest_search, suggest_bpm, suggest_key):
    """Suggests tracks based on what you've played before,

    fitting within a BPM range or sharing a musical key.
    """
    def update_user_interaction_helper(user):
        user.WANTS_TO_SUGGEST_SEARCH = True
        log.debug("Entered suggestion mode.")
        if (
            suggest_bpm
            and suggest_search == "0"
            and suggest_key
        ):
            log.debug("Entered key and BPM suggestion report.")
            user.WANTS_SUGGEST_KEY_AND_BPM_REPORT = True
        elif (suggest_bpm and suggest_search != "0"
              and suggest_key):
            log.error("You can't combine BPM and key with Track-combination report.")
            raise SystemExit(1)
        elif suggest_bpm and suggest_search != "0":
            log.error("You can't combine BPM with Track-combination report.")
            raise SystemExit(1)
        elif suggest_key and suggest_search != "0":
            log.error("You can't combine key with Track-combination report.")
            raise SystemExit(1)
        elif suggest_bpm and suggest_search == "0":
            log.debug("Entered BPM suggestion report.")
            user.WANTS_SUGGEST_BPM_REPORT = True
        elif suggest_key and suggest_search == "0":
            log.debug("Entered musical key suggestion report.")
            user.WANTS_SUGGEST_KEY_REPORT = True
        elif suggest_search == "0":
            log.debug("Entered Track-combination report. No searchterm.")
        else:
            log.debug("Entered Track-combination report.")
            user.WANTS_SUGGEST_TRACK_REPORT = True
        # log.error("track search not implemented yet.")
        # raise SystemExit(1)
        return user

    user = update_user_interaction_helper(helper)
    log.debug("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    coll_ctrl = CollectionControlCommandline(
        False, user, user.conf.discogs_token, user.conf.discogs_appid,
        user.conf.discobase, user.conf.musicbrainz_user,
        user.conf.musicbrainz_password)

    if user.WANTS_SUGGEST_TRACK_REPORT:
        coll_ctrl.track_report(suggest_search)
    if user.WANTS_SUGGEST_BPM_REPORT:
        coll_ctrl.bpm_report(suggest_bpm, 6)
    if user.WANTS_SUGGEST_KEY_REPORT:
        coll_ctrl.key_report(suggest_key)
    if user.WANTS_SUGGEST_KEY_AND_BPM_REPORT:
        coll_ctrl.key_and_bpm_report(suggest_key, suggest_bpm, 6)

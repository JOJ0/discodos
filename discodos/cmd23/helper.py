import logging
from click import Group

log = logging.getLogger('discodos')


class AbbreviationGroup(Group):
    """A version of click.Group allowing abbreviated commands."""
    def get_command(self, ctx, cmd_name):
        # Match full command name first
        if command := super().get_command(ctx, cmd_name):
            return command

        # Allow abbreviated commands
        matches = [
            command
            for command in self.list_commands(ctx)
            if command.startswith(cmd_name)
        ]
        if not matches:
            return None  # No match
        if len(matches) == 1:
            return super().get_command(ctx, matches[0])  # Unique match
        ctx.fail(f"Ambiguous command '{cmd_name}'. Matches: {', '.join(matches)}")


class User():
    """ CLI user interaction class - holds info about what user wants to do,
    """
    def __init__(self, conf, verbose, offline):  # pylint: disable=too-many-statements
        self.conf = conf
        self.verbose = verbose
        self.set_console_log_level()
        # General
        self.WANTS_ONLINE = False if offline else True
        self.DID_NOT_PROVIDE_COMMAND = False
        # Search
        self.WANTS_TO_LIST_ALL_RELEASES = False
        self.WANTS_TO_SEARCH_FOR_RELEASE = False
        # Mix
        self.WANTS_TO_ADD_TO_MIX = False
        self.WANTS_TO_SHOW_MIX_OVERVIEW = False
        self.WANTS_TO_SHOW_MIX_TRACKLIST = False
        self.WANTS_TO_CREATE_MIX = False
        self.WANTS_TO_EDIT_MIX_TRACK = False
        self.WANTS_TO_PULL_TRACK_INFO = False
        self.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE = False
        self.WANTS_VERBOSE_MIX_TRACKLIST = False
        self.WANTS_TO_REORDER_MIX_TRACKLIST = False
        self.WANTS_TO_ADD_AT_POSITION = False
        self.WANTS_TO_DELETE_MIX_TRACK = False
        self.WANTS_TO_ADD_RELEASE_IN_MIX_MODE = False
        self.WANTS_TO_ADD_AT_POS_IN_MIX_MODE = False
        self.WANTS_TO_COPY_MIX = False
        self.WANTS_TO_DELETE_MIX = False
        self.WANTS_TO_EDIT_MIX = False
        # Suggest & Bulk Edit
        self.WANTS_SUGGEST_TRACK_REPORT = False
        self.WANTS_TO_BULK_EDIT = False
        self.WANTS_SUGGEST_BPM_REPORT = False
        self.WANTS_SUGGEST_KEY_REPORT = False
        self.WANTS_SUGGEST_KEY_AND_BPM_REPORT = False
        # Brainz
        self.WANTS_TO_PULL_BRAINZ_INFO = False
        self.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = False
        self.BRAINZ_SEARCH_DETAIL = 1
        self.BRAINZ_FORCE_UPDATE = False
        self.BRAINZ_SKIP_UNMATCHED = False
        self.WANTS_MUSICBRAINZ_MIX_TRACKLIST = False
        # Search & Update
        self.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS = False
        self.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ = False
        # Import & Add
        self.WANTS_TO_IMPORT_COLLECTION = False
        self.WANTS_TO_IMPORT_RELEASE = False
        self.WANTS_TO_ADD_AND_IMPORT_RELEASE = False
        self.WANTS_TO_IMPORT_RELEASE_WITH_TRACKS = False
        self.WANTS_TO_ADD_AND_IMPORT_RELEASE_WITH_TRACKS = False
        self.WANTS_TO_REMOVE_AND_DELETE_RELEASE = False
        self.WANTS_TO_IMPORT_COLLECTION_WITH_TRACKS = False
        self.WANTS_TO_IMPORT_COLLECTION_WITH_BRAINZ = False
        # Misc
        self.WANTS_TO_SEARCH_AND_EDIT_TRACK = False
        self.RESUME_OFFSET = 0
        self.WANTS_TO_LAUNCH_SETUP = False
        self.WANTS_TO_FORCE_UPGRADE_SCHEMA = False
        self.MIX_SORT = False
        self.WANTS_TO_SHOW_STATS = False
        self.TABLE_FORMAT_OVERRIDE = False
        # Sales
        self.WANTS_TO_ADD_SALES_LISTING = False
        self.WANTS_TO_EDIT_SALES_LISTING = False

    def set_console_log_level(self):
        """ Handles console log level setting.

        Check if console log level should be left default, set as defined in
        config file, or set as requested by an override via --verbose.

        Expects a global variable named log containing a logger object (The
        logger 'discodos' we get at the top of this file). Handler index 0 is
        supposed to be the console logger we are about to alter.
        """
        log.info(
            "Console log level set to {} via config.yaml or default".format(
                logging.getLevelName(log.handlers[0].level))
        )
        # Sets log level to WARN going more verbose for each new -v.
        cli_level = max(3 - self.verbose, 0) * 10
        if cli_level < log.handlers[0].level:  # 10=DEBUG, 20=INFO, 30=WARNING
            log.handlers[0].setLevel(cli_level)
            log.warning(
                "Console log level set to {} via override from CLI.".format(
                    logging.getLevelName(log.handlers[0].level))
            )

import logging

log = logging.getLogger('discodos')


class User_int(object):
    """ CLI user interaction class - holds info about what user wants to do,

    analyzes argparser args and puts it into nicely human readable properties.
    """
    def __init__(self, _args):
        self.args = _args
        self.WANTS_ONLINE = True
        self.WANTS_TO_LIST_ALL_RELEASES = False
        self.WANTS_TO_SEARCH_FOR_RELEASE = False
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
        self.WANTS_SUGGEST_TRACK_REPORT = False
        self.WANTS_TO_BULK_EDIT = False
        self.WANTS_SUGGEST_BPM_REPORT = False
        self.WANTS_SUGGEST_KEY_REPORT = False
        self.WANTS_SUGGEST_KEY_AND_BPM_REPORT = False
        self.WANTS_TO_PULL_BRAINZ_INFO = False
        self.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = False
        self.BRAINZ_SEARCH_DETAIL = 1
        self.BRAINZ_FORCE_UPDATE = False
        self.BRAINZ_SKIP_UNMATCHED = False
        self.WANTS_MUSICBRAINZ_MIX_TRACKLIST = False
        self.WANTS_TO_EDIT_MIX = False
        self.DID_NOT_PROVIDE_COMMAND = False
        self.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS = False
        self.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ = False
        self.WANTS_TO_IMPORT_COLLECTION = False
        self.WANTS_TO_IMPORT_RELEASE = False
        self.WANTS_TO_ADD_AND_IMPORT_RELEASE = False
        self.WANTS_TO_IMPORT_COLLECTION_WITH_TRACKS = False
        self.WANTS_TO_IMPORT_COLLECTION_WITH_BRAINZ = False
        self.WANTS_TO_SEARCH_AND_EDIT_TRACK = False
        self.RESUME_OFFSET = 0
        self.WANTS_TO_LAUNCH_SETUP = False
        self.WANTS_TO_FORCE_UPGRADE_SCHEMA = False
        self.MIX_SORT = False
        self.WANTS_TO_SHOW_STATS = False


        # RELEASE MODE:
        if 'release_search' in self.args:
            if self.args.release_search == "all":
                if self.args.search_discogs_update is True:
                    # discogs update all
                    self.WANTS_ONLINE = True
                    self.WANTS_TO_LIST_ALL_RELEASES = True
                    self.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS = True
                    if self.args.search_offset > 0:
                        self.RESUME_OFFSET = self.args.search_offset
                        m_r ='Resuming is not possible in combination with '
                        m_r+='"search all -u/--discogs-update". Try it with '
                        m_r+='"mix -u/--discogs-update". Also it works '
                        m_r+='together with "import -zz/brainz-update" '
                        m_r+='and "mix -zz/--brainz-update"'
                        log.error(m_r)
                        raise SystemExit(1)
                elif self.args.search_brainz_update != 0:
                    # brainz update all
                    self.WANTS_ONLINE = True
                    self.WANTS_TO_LIST_ALL_RELEASES = True
                    self.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ = True
                    if self.args.search_brainz_update > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2
                    if self.args.search_offset > 0:
                        self.RESUME_OFFSET = self.args.search_offset
                else:
                    # just list all
                    self.WANTS_ONLINE = False
                    self.WANTS_TO_LIST_ALL_RELEASES = True
            else:
                self.WANTS_TO_SEARCH_FOR_RELEASE = True
                if (
                    self.args.add_to_mix != 0
                    and self.args.track_to_add != 0
                    and self.args.add_at_pos
                ):
                    self.WANTS_TO_ADD_AT_POSITION = True
                if self.args.add_to_mix !=0 and self.args.track_to_add !=0:
                    self.WANTS_TO_ADD_TO_MIX = True
                if self.args.add_to_mix !=0:
                    self.WANTS_TO_ADD_TO_MIX = True

                if self.args.search_discogs_update !=0:
                    if self.args.offline_mode is True:
                        log.error("You can't do that in offline mode!")
                        raise SystemExit(1)
                    self.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS = True
                elif self.args.search_brainz_update !=0:
                    if self.args.offline_mode is True:
                        log.error("You can't do that in offline mode!")
                        raise SystemExit(1)
                    self.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ = True
                    self.BRAINZ_SEARCH_DETAIL = self.args.search_brainz_update
                    if self.args.search_brainz_update > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2
                elif self.args.search_edit_track is True:
                    self.WANTS_TO_SEARCH_AND_EDIT_TRACK = True


        # MIX MODE
        if 'mix_name' in self.args:
            self.TABLE_FORMAT_OVERRIDE = self.args.table_format
            if self.args.mix_name == "all":
                self.WANTS_TO_SHOW_MIX_OVERVIEW = True
                self.WANTS_ONLINE = False
                if self.args.create_mix is True:
                    log.error("Please provide a mix name to be created!")
                    log.error("(Mix name \"all\" is not valid.)")
                    raise SystemExit(1)
                elif self.args.delete_mix is True:
                    log.error("Please provide a mix name or ID to be deleted!")
                    raise SystemExit(1)
                if self.args.discogs_update:
                    self.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    if self.args.mix_offset > 0:
                        self.RESUME_OFFSET = self.args.mix_offset
                if self.args.brainz_update:
                    self.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    self.BRAINZ_SEARCH_DETAIL = self.args.brainz_update
                    if self.args.brainz_update > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2
                    if self.args.mix_offset > 0:
                        self.RESUME_OFFSET = self.args.mix_offset
            else:
                self.WANTS_TO_SHOW_MIX_TRACKLIST = True
                self.WANTS_ONLINE = False
                if self.args.mix_sort:
                    self.MIX_SORT = self.args.mix_sort
                if self.args.create_mix:
                    self.WANTS_TO_CREATE_MIX = True
                    self.WANTS_ONLINE = False
                if self.args.edit_mix_track:
                    self.WANTS_TO_EDIT_MIX_TRACK = True
                    self.WANTS_ONLINE = False
                if self.args.verbose_tracklist == 1:
                    self.WANTS_VERBOSE_MIX_TRACKLIST = True
                    self.WANTS_ONLINE = False
                if self.args.verbose_tracklist == 2:
                    self.WANTS_MUSICBRAINZ_MIX_TRACKLIST = True
                    self.WANTS_ONLINE = False
                if self.args.reorder_from_pos:
                    self.WANTS_TO_REORDER_MIX_TRACKLIST = True
                    self.WANTS_ONLINE = False
                if self.args.delete_track_pos:
                    self.WANTS_TO_DELETE_MIX_TRACK = True
                    self.WANTS_ONLINE = False
                if self.args.add_release_to_mix:
                    self.WANTS_TO_ADD_RELEASE_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    if self.args.mix_mode_add_at_pos:
                        self.WANTS_TO_ADD_AT_POS_IN_MIX_MODE = True
                if self.args.copy_mix:
                    self.WANTS_TO_COPY_MIX = True
                    self.WANTS_ONLINE = False
                if self.args.discogs_update:
                    self.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    if self.args.mix_offset > 0:
                        m_r ="Resuming is not possible in single-mix "
                        m_r+="-u/--discogs-update. "
                        m_r+="Use -p/--pos instead."
                        log.error(m_r)
                        raise SystemExit(1)
                if self.args.delete_mix:
                    self.WANTS_TO_DELETE_MIX = True
                    self.WANTS_ONLINE = False
                if self.args.bulk_edit:
                    self.WANTS_TO_BULK_EDIT = True
                if self.args.brainz_update:
                    self.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    self.BRAINZ_SEARCH_DETAIL = self.args.brainz_update
                    if self.args.brainz_update > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2
                    if self.args.mix_offset > 0:
                        m_r ="Resuming is not possible in single-mix "
                        m_r+="-z/--brainz-update. "
                        m_r+="Use -p/--pos instead."
                        log.error(m_r)
                        raise SystemExit(1)
                if self.args.edit_mix:
                    self.WANTS_TO_EDIT_MIX = True
                    self.WANTS_ONLINE = False


        # SUGGEST MODE
        if 'suggest_search' in self.args:
            self.WANTS_TO_SUGGEST_SEARCH = True
            log.debug("Entered suggestion mode.")
            if (
                self.args.suggest_bpm
                and self.args.suggest_search == "0"
                and self.args.suggest_key
            ):
                log.debug("Entered key and BPM suggestion report.")
                self.WANTS_SUGGEST_KEY_AND_BPM_REPORT = True
            elif (self.args.suggest_bpm and self.args.suggest_search != "0"
                  and self.args.suggest_key):
                log.error("You can't combine BPM and key with Track-combination report.")
                raise SystemExit(1)
            elif self.args.suggest_bpm and self.args.suggest_search != "0":
                log.error("You can't combine BPM with Track-combination report.")
                raise SystemExit(1)
            elif self.args.suggest_key and self.args.suggest_search != "0":
                log.error("You can't combine key with Track-combination report.")
                raise SystemExit(1)
            elif self.args.suggest_bpm and self.args.suggest_search == "0":
                log.debug("Entered BPM suggestion report.")
                self.WANTS_SUGGEST_BPM_REPORT = True
            elif self.args.suggest_key and self.args.suggest_search == "0":
                log.debug("Entered musical key suggestion report.")
                self.WANTS_SUGGEST_KEY_REPORT = True
            elif self.args.suggest_search == "0":
                log.debug("Entered Track-combination report. No searchterm.")
            else:
                log.debug("Entered Track-combination report.")
                self.WANTS_SUGGEST_TRACK_REPORT = True
            # log.error("track search not implemented yet.")
            # raise SystemExit(1)


        # IMPORT MODE
        if 'import_id' in self.args:
            log.debug("Entered import mode.")
            if self.args.import_id != 0 and self.args.import_add_coll:
                self.WANTS_TO_ADD_AND_IMPORT_RELEASE = True
            elif self.args.import_id == 0 and self.args.import_add_coll:
                log.error("Release ID missing. Which release should we add to "
                          "collection and import?")
                raise SystemExit(1)
            elif self.args.import_id == 0:
                if self.args.import_tracks:
                    self.WANTS_TO_IMPORT_COLLECTION_WITH_TRACKS = True
                    if self.args.import_offset > 0:
                        self.RESUME_OFFSET = self.args.import_offset
                        m_r ='Resuming is not possible in combination with '
                        m_r+='"import -u/--discogs-update". Try it with '
                        m_r+='"mix -u/--discogs-update". Also it works '
                        m_r+='together with "import -zz/brainz-update" '
                        m_r+='and "mix -zz/--brainz-update"'
                        log.error(m_r)
                        raise SystemExit(1)
                elif self.args.import_brainz:
                    self.WANTS_TO_IMPORT_COLLECTION_WITH_BRAINZ = True
                    self.BRAINZ_SEARCH_DETAIL = self.args.import_brainz
                    if self.args.import_brainz > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2
                    if self.args.import_brainz_force:
                        self.BRAINZ_FORCE_UPDATE = True
                    if self.args.import_brainz_skip_unmatched:
                        self.BRAINZ_SKIP_UNMATCHED = True
                    if self.args.import_offset > 0:
                        self.RESUME_OFFSET = self.args.import_offset
                else:
                    self.WANTS_TO_IMPORT_COLLECTION = True
            else:
                if self.args.import_brainz or self.args.import_tracks:
                    log.error("You can't combine a single release import with "
                              "-z or -u.")
                    raise SystemExit(1)
                else:
                    self.WANTS_TO_IMPORT_RELEASE = True


        # STATS MODE
        if self.args.command == 'stats':
            log.debug("Entered stats mode.")
            self.WANTS_TO_SHOW_STATS = True


        # SETUP MODE
        if self.args.command == 'setup':
            log.debug("Entered setup mode.")
            self.WANTS_TO_LAUNCH_SETUP = True
            if self.args.force_upgrade_schema is True:
                self.WANTS_TO_FORCE_UPGRADE_SCHEMA = True


        # NO COMMAND - SHOW HELP
        if self.args.command is None:
            self.DID_NOT_PROVIDE_COMMAND = True

        if self.args.offline_mode is True:
            self.WANTS_ONLINE = False

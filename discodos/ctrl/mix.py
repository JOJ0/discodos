import logging
from abc import ABC
# import pprint as p

from discodos.ctrl.common import ControlCommon
from discodos.model import Mix
from discodos.utils import is_number
from discodos.view import MixViewCommandline

log = logging.getLogger('discodos')


# mix controller class (abstract) - common attrs and methods  for gui and cli
class MixControlCommon (ABC):
    """Common controller functionality for mixes"""
    def __init__(self):
        pass


# mix controller class CLI implementation
class MixControlCommandline (ControlCommon, MixControlCommon):
    """Controls CLI logic for mixes """

    def __init__(self, db_conn, mix_name_or_id, _user_int, db_file = False):
        self.user = _user_int # take an instance of the User_int class and set as attribute
        self.cli = MixViewCommandline() # instantiatie the Mix view class (the CLI)
        self.mix = Mix(db_conn, mix_name_or_id, db_file) # instantiate the Mix model class
        if self.mix.db_not_found == True:
            self.cli.ask('Setting up DiscoBASE, press enter...')
            super(MixControlCommandline, self).setup_db(db_file)
            self.mix = Mix(db_conn, db_file)

    def create(self):
        if is_number(self.mix.name_or_id):
            log.error("Mix name can't be a number!")
        else:
            if self.mix.name_existing:
                log.error('Mix "{}" already existing.'.format(self.mix.name))
                raise SystemExit(1)
            self.cli.p('Creating new mix "{}".'.format(self.mix.name))
            answers = self._create_ask_details()
            created_id = self.mix.create(answers['played'], answers['venue'])
            self.cli.p('New mix created with ID {}.'.format(created_id))
            self.view_mixes_list()

    def _create_ask_details(self):
        played = self.cli.ask("When did you (last) play it? eg 2018-01-01 ")
        venue = self.cli.ask(text="And where? ")
        return {'played': played, 'venue': venue}

    def view_mixes_list(self):
        ''' view a list of all mixes '''
        mixes_data = self.mix.get_all_mixes(order_by='played DESC')
        #mixes_data = self.mix.get_all_mixes(order_by='venue, played DESC')
        self.cli.tab_mixes_list(mixes_data)

    def view(self):
        if self.mix.id_existing:
            self.cli.tab_mix_info_header(self.mix.get_mix_info())
            if self.user.WANTS_VERBOSE_MIX_TRACKLIST:
                full_mix = self.mix.get_full_mix(verbose=True, order_by=self.user.MIX_SORT)
            elif self.user.WANTS_MUSICBRAINZ_MIX_TRACKLIST:
                full_mix = self.mix.get_full_mix(brainz=True, order_by=self.user.MIX_SORT)
            else:
                full_mix = self.mix.get_full_mix(verbose=False, order_by=self.user.MIX_SORT)

            if not full_mix:
                self.cli.p("No tracks in mix yet.")
            else:
                if self.user.WANTS_VERBOSE_MIX_TRACKLIST:
                    self.cli.tab_mix_table(
                        full_mix, _verbose = True,
                        format=self.user.TABLE_FORMAT_OVERRIDE
                    )
                elif self.user.WANTS_MUSICBRAINZ_MIX_TRACKLIST:
                    self.cli.tab_mix_table(
                        full_mix, brainz = True,
                        format=self.user.TABLE_FORMAT_OVERRIDE
                    )
                else:
                    self.cli.tab_mix_table(
                        full_mix, _verbose = False,
                        format=self.user.TABLE_FORMAT_OVERRIDE
                    )
        else:
            self.cli.p("Mix \"{}\" is not existing yet!".format(self.mix.name_or_id))

    def delete(self):
        if self.mix.id_existing:
            if self.cli.really_delete_mix(self.mix.id, self.mix.name):
                if self.mix.delete():
                    self.cli.p(
                      'Mix "{} - {}" deleted successfully.'.format(
                          self.mix.id, self.mix.name))
        else:
           self.cli.p("Mix \"{}\" doesn't exist.".format(self.mix.name_or_id))

    def edit_track(self, edit_track):
        if self.mix.id_existing:
            msg_editing ='Editing track {} in "{}".\n'.format(edit_track, self.mix.name)
            msg_editing+='* to keep a value as is, press enter\n'
            msg_editing+='* text in (braces) shows current value'
            self.cli.p(msg_editing)
            track_details = self.mix.get_one_mix_track(edit_track)
            if track_details:
                self.cli.p("{} - {} - {}".format(
                           track_details['discogs_title'],
                           track_details['d_track_no'],
                           track_details['d_track_name']))
                log.info("current d_release_id: %s", track_details['d_release_id'])
                edit_answers = self.cli.edit_ask_details(track_details,
                        self.cli._edit_track_questions)
                for a in edit_answers.items():
                    log.info("answers: %s", str(a))
                update_ok = self.mix.update_mix_track_and_track_ext(track_details, edit_answers)
                if update_ok:
                    self.cli.p("Track edit was successful.")
                else:
                    log.error("Something went wrong on mix_track edit!")
                    raise SystemExit(1)
                self.view()
            else:
                self.cli.p("No track "+edit_track+" in \""+
                            self.mix.name+"\".")
        else:
            self.cli.p("Mix unknown: \"{}\".".format(self.mix.name_or_id))

    def edit_mix(self):
        if self.mix.id_existing:
            msg_editing ='Editing mix {}\n'.format(self.mix.name)
            msg_editing+='* to keep a value as is, press enter\n'
            msg_editing+='* text in (braces) shows current value'
            self.cli.p(msg_editing)
            mix_details = self.mix.get_mix_info()
            if mix_details:
                self.cli.p("{} - {} - {}".format(
                           mix_details['name'],
                           mix_details['played'],
                           mix_details['venue']))
                edit_answers = self.cli.edit_ask_details(mix_details,
                        self.cli._edit_mix_questions)
                check_name = None
                for key,a in edit_answers.items():
                    log.info("answers: %s:%s", key, str(a))
                    if key == 'name':
                        check_name = self.mix._get_mix_id(a)
                if check_name != None:
                    log.warning("Name already taken. Dropping name-edit from update.")
                    del(edit_answers['name'])
                update_ok = self.mix.update_mix_info(mix_details, edit_answers)
                if update_ok:
                    self.cli.p("Mix edit was successful.")
                else:
                    log.error("Something went wrong on mix edit!")
                    raise SystemExit(1)
                # on dup-name err, don't show mixes list, user should see warning
                if check_name == None:
                    self.view_mixes_list()
            else:
                self.cli.p("Mix details couldn't be fetched.")
        else:
            self.cli.p('Mix unknown: "{}".'.format(self.mix.name_or_id))

    def bulk_edit_tracks(self, fields_str, first_track):
        log.debug("bulk_edit_tracks args: {} {}".format(fields_str, first_track))
        fields_list = fields_str.split(',')
        log.debug('fields split: {}'.format(fields_list))
        if not first_track:
            first_track = 1
        if self.mix.id_existing:
            for track in self.mix.get_full_mix(verbose = True):
                if not track['track_pos'] < first_track:
                    self.cli.p(
                           "Editing track {}  |  {} - {}  |  {} - {}".format(
                           track['track_pos'], track['discogs_title'], track['d_track_no'],
                           track['d_artist'], track['d_track_name']))
                    track_details = self.mix.get_one_mix_track(track['track_pos'])
                    bulk_questions = []
                    for field in fields_list:
                        #field=field.replace('d_', '')
                        #log.info("checking field: {}".format(field))
                        for question in self.cli._edit_track_questions:
                            if field == question[0]:
                                #log.info("appending to bulk_questions list")
                                bulk_questions.append(question)
                    log.debug("CTRL: bulk_questions: {}".format(bulk_questions))
                    edit_answers = self.cli.edit_ask_details(track_details,
                        bulk_questions)
                    self.mix.update_mix_track_and_track_ext(track_details,
                          edit_answers)
                    print("") # just some space

    def reorder_tracks(self, startpos = 1):
        reordered = self.mix.reorder_tracks(int(startpos))
        if not reordered:
            log.error("Reorder failed. No track {} in mix.".format(startpos))
        else:
            log.info("Reordering tracks successful")
            self.view()

    def delete_track(self, delete_track_pos):
        if self.cli.really_delete_track(delete_track_pos, self.mix.name):
             successful = self.mix.delete_track(delete_track_pos)
             # reorder existing and print tracklist
             if successful:
                 if delete_track_pos == 1:
                    self.mix.reorder_tracks(1)
                 else:
                    self.mix.reorder_tracks(delete_track_pos - 1)
                 self.view()
             else:
                 self.cli.p("Delete failed, maybe nonexistent track position?")

    # definitely cli specific

    def add_offline_track(self, rel_list, track_no, pos):
        if rel_list:
            self._add_track(rel_list[0][0], rel_list[0][1], track_no, pos)

    def add_discogs_track(self, release_details, track_no, pos, track_no_suggest = ''):
        log.info("add_discogs_track got this release_details: {}".format(
          release_details))
        if release_details:
            if not track_no:
                track_no = self.cli.ask_for_track(suggest = track_no_suggest)
            self._add_track(release_details['id'], release_details['title'],
              track_no, pos)
        else:
            log.error("No release to add to mix.")

    def _add_track(self, _release_id, _release_title, _track_no, _pos):
        """Low-level track add method,

        intended to only be called from add_offline_track()
        and add_discogs_track()
        """
        if not _track_no:
            track_to_add = self.cli.ask_for_track()
        else:
            log.debug("_track_no was given, value is {}".format(_track_no))
            track_to_add = _track_no
        if _pos == None:
            log.debug("_pos was None, setting to 0")
            _pos = 0
        log.debug("This is _pos: {}".format(_pos))
        log.debug("This is track_to_add: {}".format(track_to_add))
        log.debug("This is _release_id: %s", _release_id)
        log.debug("This is _release_title: %s", _release_title)
        if self.mix.id_existing:
            last_track = self.mix.get_last_track()
            log.debug("Currently last track in mix is: %s", last_track[0])
            current_id = False
            if _pos:
                # a position to squeeze in the track was given
                # get current tracks >= pos
                tracks_to_shift = self.mix.get_tracks_from_position(_pos)
                if self.cli.really_add_track(track_to_add, _release_title,
                                             self.mix.id, _pos):
                    current_id = self.mix.add_track(_release_id,
                                                    track_to_add, track_pos = _pos)
                    # all good? reorder tracks
                    if current_id:
                        log.info("Add track to mix successful, now reordering ...")
                        self.mix.reorder_tracks_squeeze_in(_pos, tracks_to_shift)
                else:
                    print("Track not added.")
                    return True
            elif is_number(last_track[0]):
                # no position was given, tracks already mix
                if self.cli.really_add_track(track_to_add, _release_title,
                                             self.mix.id, last_track[0]+1):

                    current_id = self.mix.add_track(_release_id,
                                                    track_to_add, track_pos = last_track[0] + 1)
                else:
                    print("Track not added.")
                    return True
            else:
                # no position and it's the first track ever added
                if self.cli.really_add_track(track_to_add, _release_title,
                                             self.mix.id, 1):

                    current_id = self.mix.add_track(_release_id,
                                                    track_to_add, track_pos = 1)
                else:
                    print("Track not added.")
                    return True
            # FIXME untested if this is actually a proper sanity check
            log.debug("Value of current_id in add_offline_track: {}".format(current_id))
            if current_id:
                self.view()
                #return True
            else:
                log.error("Add track to DB failed!")
                #return False
        else:
            self.cli.p("Mix ID {} is not existing yet.".format(self.mix.id))
            return False

    def pull_track_info_from_discogs(self, coll_ctrl, start_pos=0,
          offset=0):
        if not coll_ctrl.ONLINE:
            self.cli.p("Not online, can't pull from Discogs...")
            return False # exit method we are offline

        if self.mix.id_existing:
            self.cli.p(
             "Let's update current mixes tracks with info from Discogs...")
            mixed_tracks = self.mix.get_mix_tracks_for_brainz_update(start_pos)
        else:
            self.cli.p(
             "Let's update every track contained in any mix with info from Discogs...")
            mixed_tracks = self.mix.get_all_mix_tracks_for_brainz_update(offset)

        if offset:
            update_ret = coll_ctrl.update_tracks_from_discogs(mixed_tracks,
              offset)
        else:
            update_ret = coll_ctrl.update_tracks_from_discogs(mixed_tracks,
              start_pos)

        return update_ret

    def update_track_info_from_brainz(self, coll_ctrl, start_pos=0,
          detail=1, offset=0):
        if not coll_ctrl.ONLINE:
            self.cli.p("Not online, can't pull from AcousticBrainz...")
            return False # exit method we are offline

        if self.mix.id_existing:
            self.cli.p(
             "Let's update current mixes tracks with info from AcousticBrainz...")
            mixed_tracks = self.mix.get_mix_tracks_for_brainz_update(
              start_pos)
        else:
            self.cli.p(
             "Let's update every track contained in any mix with info from AcousticBrainz...")
            mixed_tracks = self.mix.get_all_mix_tracks_for_brainz_update(
              offset)

        if offset:
            match_ret = coll_ctrl.update_tracks_from_brainz(mixed_tracks,
              detail, offset)
        else:
            match_ret = coll_ctrl.update_tracks_from_brainz(mixed_tracks,
              detail, start_pos)

        return match_ret

    def copy_mix(self):
        self.cli.p("Copying mix {} - {}.".format(self.mix.id, self.mix.name))
        copy_tr = self.mix.get_tracks_of_one_mix()
        new_mix_name = self.cli.ask("How should the copy be named? ")
        new_mix = Mix(self.mix.db_conn, new_mix_name)
        db_return_new = new_mix.create(self.mix.played, self.mix.venue, new_mix_name)
        if db_return_new:
            for tr in copy_tr:
                log.debug("CTRL copy_mix data: {}, {}, {}, {}, {}, ".format(
                    tr["d_release_id"], tr["d_track_no"], tr["track_pos"], tr["trans_rating"],
                    tr["trans_notes"]))
                new_mix.add_track(tr["d_release_id"], tr["d_track_no"], tr["track_pos"], tr["trans_rating"],
                    tr["trans_notes"])
            new_mix.db_conn.commit()
            self.cli.p("Copy mix successful. New ID is {}.".format(new_mix.id))
            return True
        else:
            log.error("Copy mix failed. Couldn't create.")
            return False

    def update_in_d_coll(self, coll_ctrl, start_pos = False):
        if coll_ctrl.ONLINE:
            if self.mix.id_existing:
                self.cli.p("Let's update Discogs collection field in current mixes releases...")
                #db_releases = self.mix.get_releases_of_one_mix(start_pos)
                #for db_rel in db_releases:
                #    pass
            #else:
            #    self.cli.p("Let's update ALL tracks in ALL mixes with info from Discogs...")
            #    mixed_tracks = self.mix.get_all_tracks_in_mixes()

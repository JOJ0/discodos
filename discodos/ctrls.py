from discodos.utils import is_number, join_sep
from discodos.models import Mix, Collection, Brainz, Brainz_match
from discodos.views import Mix_view_cli, Collection_view_cli
from abc import ABC, abstractmethod
from discodos import log
import discogs_client.exceptions as errors
import pprint as p
import re
from time import time

# mix controller class (abstract) - common attrs and methods  for gui and cli
class Mix_ctrl_common (ABC):
    def __init__(self):
        pass

# mix controller class CLI implementation
class Mix_ctrl_cli (Mix_ctrl_common):

    def __init__(self, db_conn, mix_name_or_id, _user_int, db_file = False):
        self.mix = Mix(db_conn, mix_name_or_id, db_file) # instantiate the Mix model class
        self.cli = Mix_view_cli() # instantiatie the Mix view class (the CLI)
        self.user = _user_int # take an instance of the User_int class and set as attribute

    def create(self):
        if is_number(self.mix.name_or_id):
            log.error("Mix name can't be a number!") # log is everywhere, also in view
        else:
            self.cli.p("Creating new mix \"{}\".".format(self.mix.name)) # view
            answers = self._create_ask_details() # view with questions from common
            created_id = self.mix.create(answers['played'], answers['venue']) # model
            self.mix.db_conn.commit() # model
            self.cli.p("New mix created with ID {}.".format(created_id)) # view
            self.view_mixes_list() # view

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
                full_mix = self.mix.get_full_mix(verbose = True)
            elif self.user.WANTS_MUSICBRAINZ_MIX_TRACKLIST:
                full_mix = self.mix.get_full_mix(brainz = True)
            else:
                full_mix = self.mix.get_full_mix(verbose = False)

            if not full_mix:
                self.cli.p("No tracks in mix yet.")
            else:
                if self.user.WANTS_VERBOSE_MIX_TRACKLIST:
                    self.cli.tab_mix_table(full_mix, _verbose = True)
                elif self.user.WANTS_MUSICBRAINZ_MIX_TRACKLIST:
                    self.cli.tab_mix_table(full_mix, brainz = True)
                else:
                    self.cli.tab_mix_table(full_mix, _verbose = False)
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
                for a in edit_answers.items():
                    log.info("answers: %s", str(a))
                update_ok = self.mix.update_mix_info(mix_details, edit_answers)
                if update_ok:
                    self.cli.p("Mix edit was successful.")
                else:
                    log.error("Something went wrong on mix edit!")
                    raise SystemExit(1)
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
                    edit_answers = self._edit_track_ask_details(track_details,
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


    # _add_track should only be called from add_offline_track() and add_discogs_track()
    def _add_track(self, _release_id, _release_title, _track_no, _pos):
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
            elif is_number(last_track[0]):
                # no position was given, tracks already mix
                if self.cli.really_add_track(track_to_add, _release_title,
                                             self.mix.id, last_track[0]+1):

                    current_id = self.mix.add_track(_release_id,
                                                    track_to_add, track_pos = last_track[0] + 1)
            else:
                # no position and it's the first track ever added
                if self.cli.really_add_track(track_to_add, _release_title,
                                             self.mix.id, 1):

                    current_id = self.mix.add_track(_release_id,
                                                    track_to_add, track_pos = 1)
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

    def pull_track_info_from_discogs(self, coll_ctrl, start_pos = False):
        if not coll_ctrl.ONLINE:
            self.cli.p("Not online, can't pull from Discogs...")
            return False # exit method we are offline

        if self.mix.id_existing:
            self.cli.p("Let's update current mixes tracks with info from Discogs...")
            mixed_tracks = self.mix.get_mix_tracks_for_brainz_update(start_pos)
        else:
            self.cli.p("Let's update every track contained in any mix with info from Discogs...")
            mixed_tracks = self.mix.get_all_mix_tracks_for_brainz_update()

        update_ret = coll_ctrl.update_tracks_from_discogs(mixed_tracks)
        return update_ret


    def update_track_info_from_brainz(self, coll_ctrl, start_pos = False,
          detail = 1):
        def _url_match(_d_release_id, _mb_releases):
            '''finds Release MBID by looking through Discogs links.'''
            #nonlocal release_match_method
            for release in _mb_releases['release-list']:
                log.info('CTRL: ...Discogs-URL-matching MB-Release')
                log.info('CTRL: ..."{}"'.format(release['title']))
                full_mb_rel = coll_ctrl.brainz.get_mb_release_by_id(release['id'])
                #pprint.pprint(full_mb_rel) # DEBUG
                urls = coll_ctrl.brainz.get_urls_from_mb_release(full_mb_rel)
                if urls:
                    for url in urls:
                        if url['type'] == 'discogs':
                            log.info('CTRL: ...trying Discogs URL: ..{}'.format(
                                url['target'].replace('https://www.discogs.com/', '')))
                            if str(_d_release_id) in url['target']:
                                log.info(
                                  'CTRL: Found MusicBrainz match (via Discogs URL)')
                                _mb_rel_id = release['id']
                                release_match_method = 'Discogs URL'
                                return _mb_rel_id # found release match
            return False

        def _catno_match(_d_catno, _mb_releases, variations = False):
            '''finds Release MBID by looking through catalog numbers.'''
            #nonlocal release_match_method
            for release in _mb_releases['release-list']:
                _mb_rel_id = False # this is what we are looking for
                if variations:
                    log.info('CTRL: ...CatNo-matching (variation) MB-Release')
                    log.info('CTRL: ..."{}"'.format(release['title']))
                else:
                    log.info('CTRL: ...CatNo-matching (exact) MB-Release')
                    log.info('CTRL: ..."{}"'.format(release['title']))
                full_rel = coll_ctrl.brainz.get_mb_release_by_id(release['id'])
                # FIXME should we do something here if full_rel not successful?

                for mb_label_item in full_rel['release']['label-info-list']:
                    mb_catno_orig = coll_ctrl.brainz.get_catno_from_mb_label(mb_label_item)
                    mb_catno = mb_catno_orig.replace(' ', '') # strip whitespace

                    if variations == False: # this is the vanilla exact-match
                        log.info('CTRL: ...DC CatNo: {}'.format(_d_catno))
                        log.info('CTRL: ...MB CatNo: {}'.format(mb_catno))
                        if mb_catno == _d_catno:
                            release_match_method = 'CatNo (exact)'
                            _mb_rel_id = release['id']
                    else: # these are the variation matches
                        #log.info(
                        #  'CTRL: ...MB CatNo: {} (original)'.format(mb_catno))
                        if mb_catno[-1:] == 'D' or mb_catno[-1:] == 'd':
                            mb_catno = mb_catno[:-1]
                            log.info('CTRL: ...DC CatNo: {}'.format(_d_catno))
                            log.info('CTRL: ...MB CatNo: {} (D-end cut off)'.format(
                              mb_catno))
                            if mb_catno == _d_catno:
                                release_match_method = 'CatNo (var 1)'
                                _mb_rel_id = release['id']
                        else:
                            mb_numtail = re.split('[^\d]', mb_catno)[-1]
                            if mb_numtail:
                                mb_beforenum = re.split('[^\D]', mb_catno)[0]
                                mb_lastchar = mb_beforenum[-1:]
                                if  mb_lastchar == 'D' or mb_lastchar == 'd':
                                    until_d = mb_beforenum[0:-1]
                                    mb_catno = '{}{}'.format(until_d, mb_numtail)
                                    log.info('CTRL: ...DC CatNo: {}'.format(_d_catno))
                                    log.info('CTRL: ...MB CatNo: {} (D in between cut out)'.format(
                                      mb_catno))
                                    if mb_catno == _d_catno:
                                        release_match_method = 'CatNo (var 2)'
                                        _mb_rel_id = release['id']
                            else:
                                log.info('CTRL: ...no applicable variations found')

                    # only show the final log line if we found a match
                    if _mb_rel_id:
                        log.info(
                          'CTRL: Found MusicBrainz release match via {} '.format(release_match_method))
                    # always return this var - if nothing found it's False
                    return _mb_rel_id # found release match

        def _track_name_match(_d_track_name, _mb_release):
            #pprint.pprint(_mb_release) # human readable json
            #nonlocal rec_match_method
            for medium in _mb_release['release']['medium-list']:
                for track in medium['track-list']:
                    _rec_title = track['recording']['title']
                    _rec_title_low = _rec_title.lower()
                    _d_track_name_low = _d_track_name.lower()
                    if _rec_title_low == _d_track_name_low: # ignore case diffs
                        _rec_id = track['recording']['id']
                        log.info('CTRL: Track name matches: {}'.format(
                            _rec_title))
                        log.info('CTRL: Recording MBID: {}'.format(
                            _rec_id)) # finally we have a rec MBID
                        rec_match_method = 'Track Name'
                        return _rec_id
            log.info('CTRL: No track name match: {} vs. {}'.format(
                _d_track_name, _rec_title))
            return False

        def _track_no_match(_d_track_name, _d_track_no, _d_track_numerical, _mb_release):
            #pprint.pprint(_mb_release) # human readable json
            #nonlocal rec_match_method
            _d_track_numerical = int(_d_track_numerical) # make sure it's int
            for medium in _mb_release['release']['medium-list']:
                #track_count = len(medium['track-list'])
                for track in medium['track-list']:
                    _rec_title = track['recording']['title']
                    track_number = track['number'] # could be A, AA, ..
                    track_position = int(track['position']) # starts at 1, ensure int
                    if track_number == _d_track_no:
                        _rec_id = track['recording']['id']
                        log.info('CTRL: Track number matches: {}'.format(
                            _rec_title))
                        log.info('CTRL: Recording MBID: {}'.format(
                            _rec_id)) # finally we have a rec MBID
                        rec_match_method = 'Track No'
                        return _rec_id
                    elif track_position == _d_track_numerical:
                        _rec_id = track['recording']['id']
                        log.info('CTRL: Track number "numerical" matches: {}'.format(
                            _rec_title))
                        log.info('CTRL: Recording MBID: {}'.format(
                            _rec_id)) # finally we have a rec MBID
                        rec_match_method = 'Track No (num)'
                        return _rec_id
            log.info('CTRL: No track number or numerical position match: {} vs. {}'.format(
                _d_track_numerical, track_position))
            return False

        if not coll_ctrl.ONLINE:
            self.cli.p("Not online, can't pull from AcousticBrainz...")
            return False # exit method we are offline

        start_time = time()
        if self.mix.id_existing:
            self.cli.p("Let's update current mixes tracks with info from AcousticBrainz...")
            mixed_tracks = self.mix.get_mix_tracks_for_brainz_update(start_pos)
        else:
            self.cli.p("Let's update every track contained in any mix with info from AcousticBrainz...")
            mixed_tracks = self.mix.get_all_mix_tracks_for_brainz_update()

        processed, processed_total = 0, len(mixed_tracks)
        errors_not_found, errors_db, errors_no_release, errors_no_rec = 0, 0, 0, 0
        added_release, added_rec, added_key, added_chords_key, added_bpm = 0, 0, 0, 0, 0
        for mix_track in mixed_tracks:
            release_mbid, rec_mbid = None, None # we are filling these
            key, chords_key, bpm = None, None, None # searched later, in this order
            d_release_id = mix_track['d_release_id']
            d_track_no = mix_track['d_track_no']
            user_rec_mbid = mix_track['m_rec_id_override']
            processed += 1

            log.info('CTRL: Trying to match Discogs release {} "{}"...'.format(
                mix_track['d_release_id'], mix_track['discogs_title']))
            d_rel = coll_ctrl.collection.get_d_release(d_release_id) # 404 is handled here
            if not d_rel:
                log.warning("Skipping. Cant't fetch Discogs release.")
                coll_ctrl.cli.brainz_processed_so_far(processed, processed_total)
                print('')
                continue
            else:
                if not mix_track['d_track_name']: # no track name in db -> ask discogs
                    d_rel = coll_ctrl.collection.get_d_release(d_release_id) # 404 is handled here
                    d_track_name = coll_ctrl.collection.d_tracklist_parse(
                        d_rel.tracklist, mix_track['d_track_no'])
                    if not d_track_name:
                        errors_not_found += 1
                        log.warning(
                          'Skipping. Track number {} not existing on release "{}"'.format(
                           mix_track['d_track_no'], mix_track['discogs_title']))
                        coll_ctrl.cli.brainz_processed_so_far(processed, processed_total)
                        print('')
                        continue # jump to next track. space for readability ^^
                else:
                    d_track_name = mix_track['d_track_name'] # trackname in db, good

                if not mix_track['d_catno']: # no label name in db -> ask discogs
                    d_catno = d_rel.labels[0].data['catno']
                else:
                    d_catno = mix_track['d_catno']

                # get_discogs track number numerical
                #print(dir(d_rel.tracklist[1]))
                #d_rel_track_count = len(d_rel.tracklist)
                d_track_numerical = coll_ctrl.collection.d_tracklist_parse_numerical(
                    d_rel.tracklist, d_track_no)

            # initialize the brainz match class here,
            # we pass it the prepared track data we'd like to match,
            # detailed modifications are done inside (strip spaces, etc)
            bmatch = Brainz_match(coll_ctrl.brainz.musicbrainz_user,
                                  coll_ctrl.brainz.musicbrainz_password,
                                  coll_ctrl.brainz.musicbrainz_appid,
              d_release_id, mix_track['discogs_title'], d_catno,
              mix_track['d_artist'], d_track_name, d_track_no,
              d_track_numerical)
            # fetching of mb_releases controllable from outside
            # (reruns with different settings)
            bmatch.fetch_mb_releases(detail = detail)
            release_mbid = bmatch.match_release()
            if not release_mbid and not user_rec_mbid:
                log.info('CTRL: No MusicBrainz release matches. Sorry dude!')
            else: # Recording MBID search
                if user_rec_mbid:
                    rec_mbid = user_rec_mbid
                else:
                    bmatch.fetch_mb_matched_rel()
                    rec_mbid = bmatch.match_recording()

                if rec_mbid: # we where lucky...
                    # get accousticbrainz info
                    key = bmatch.get_accbr_key(rec_mbid)
                    chords_key = bmatch.get_accbr_key(rec_mbid)
                    bpm = bmatch.get_accbr_bpm(rec_mbid)
                else:
                    errors_no_rec += 1
            # user reporting starts here, not in model anymore
            # summary and save only when we have Release MBID or user_rec_mbid
            if release_mbid or user_rec_mbid:
                print("Adding Brainz info for track {} on {} ({})".format(
                    mix_track['d_track_no'],  mix_track['discogs_title'],
                    d_release_id))
                print("{} - {}".format(mix_track['d_artist'], d_track_name))
                if release_mbid:
                    print("Release MBID: {}".format(release_mbid))
                else:
                    log.warning("No Release MBID found!!!")

                if not rec_mbid:
                    log.warning("No Recording MBID found!!!")
                else:
                    if user_rec_mbid:
                        print("Recording MBID: {} (user override)".format(rec_mbid))
                    else:
                        print("Recording MBID: {}".format(rec_mbid))

                print("Key: {}, Chords Key: {}, BPM: {}".format(
                    key, chords_key, bpm))

                # update release table
                ok_release = coll_ctrl.collection.update_release_brainz(d_release_id,
                    release_mbid, bmatch.release_match_method)
                if ok_release:
                    print('Release table updated successfully.')
                    log.info('Release table updated successfully.')
                    added_release += 1
                else:
                    log.error('while updating release table. Continuing anyway.')
                    errors_db += 1

                # update track and track_ext table
                ok_rec = coll_ctrl.collection.upsert_track_brainz(d_release_id,
                    mix_track['d_track_no'], rec_mbid, bmatch.rec_match_method,
                    key, chords_key, bpm)

                if ok_rec:
                    if rec_mbid: added_rec += 1
                    print('Track table updated successfully.')
                    log.info('Track table updated successfully.')
                    if key: added_key += 1
                    if chords_key: added_chords_key += 1
                    if bpm: added_bpm += 1
                else:
                    log.error('while updating track table. Continuing anyway.')
                    errors_db += 1

            else:
                errors_no_release += 1
                log.warning('No Release MBID found for track {} on Discogs release "{}"'.format(
                        mix_track['d_track_no'], mix_track['discogs_title']))
            coll_ctrl.cli.brainz_processed_so_far(processed, processed_total)
            print('') # space for readability

        coll_ctrl.cli.brainz_processed_report(processed_total, added_release, added_rec,
          added_key, added_chords_key, added_bpm, errors_db, errors_not_found)
        self.cli.duration_stats(start_time, 'Updating track info') # print time stats
        return False # we are through all tracks in mix

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

# Collection controller common methods
class Coll_ctrl_common (ABC):

    def __init__(self):
        pass

# Collection controller class
class Coll_ctrl_cli (Coll_ctrl_common):
    '''manages the record collection, offline and with help of discogs data'''

    def __init__(self, _db_conn, _user_int, _userToken, _appIdentifier,
            _db_file = False, _musicbrainz_user = False, _musicbrainz_pass = False):
        self.user = _user_int # take an instance of the User_int class and set as attribute
        self.collection = Collection(_db_conn, _db_file)
        self.cli = Collection_view_cli() # instantiate cli frontend class 
        if self.user.WANTS_ONLINE:
            if not self.collection.discogs_connect(_userToken, _appIdentifier):
                log.error("connecting to Discogs API, let's stay offline!\n")
            else: # only try to initialize brainz if discogs is online already
                self.brainz = Brainz(_musicbrainz_user, _musicbrainz_pass, _appIdentifier)
        log.info("CTRL: Initial ONLINE status is %s", self.ONLINE)

    @property
    def ONLINE(self):
        status = self.collection.ONLINE
        log.debug("CTRL: Collection model has ONLINE status %s", status)
        return status

    @property
    def d(self):
        discogs_cli_o = self.collection.d
        log.debug("CTRL: Getting Collection.d instance from MODEL: %s", discogs_cli_o)
        return discogs_cli_o

    @property
    def me(self):
        discogs_me_o = self.collection.d
        log.debug("CTRL: Getting Collection.me instance from MODEL: %s", discogs_me_o)
        return discogs_me_o

    def search_release(self, _searchterm): # online or offline search is decided in this method
        if self.collection.ONLINE:
            if is_number(_searchterm):
                self.cli.p('Searchterm is a number, trying to add Release ID to collection...')
                if not self.add_release(int(_searchterm)):
                    log.warning("Release wasn't added to Collection, continuing anyway.")

            db_releases = self.collection.get_all_db_releases()
            self.cli.p('Searching Discogs for Release ID or Title: {}'.format(_searchterm))
            search_results = self.collection.search_release_online(_searchterm)
            # SEARCH RESULTS OUTPUT HAPPENS HERE
            compiled_results_list = self.print_and_return_first_d_release(
                  search_results, _searchterm, db_releases)
            return compiled_results_list

        else:
            self.cli.p('Searching database for ID or Title: {}'.format(_searchterm))
            search_results = self.collection.search_release_offline(_searchterm)
            if not search_results:
                self.cli.p('Nothing found.')
                return False
            else:
                if len(search_results) == 1:
                    self.cli.p('Found release: {} - {}'.format(search_results[0][3],
                                                          search_results[0][1]))
                    return search_results
                else:
                    self.cli.p('Found several releases:')
                    for cnt,release in enumerate(search_results):
                        self.cli.p('({}) {} - {}'.format(cnt, release[3], release[1]))
                    #num_search_results = [[cnt,rel] for cnt,rel in enumerate(search_results)]
                    #print(num_search_results)
                    answ = self.cli.ask('Which release? (0) ')
                    if answ == '':
                        answ = 0
                    else:
                        answ = int(answ)
                    return [search_results[answ]]
                    #return num_search_results[answ][0]

    def print_and_return_first_d_release(self, discogs_results, _searchterm, _db_releases):
        ''' formatted output _and return of Discogs release search results'''
        self.first_track_on_release = '' # reset this in any case first
        # only show pages count if it's a Release Title Search
        if not is_number(_searchterm):
            self.cli.p("Found "+str(discogs_results.pages )+" page(s) of results!")
        else:
            self.cli.p("ID: "+discogs_results[0].id+", Title: "+discogs_results[0].title+"")
        for result_item in discogs_results:
            self.cli.p("Checking " + str(result_item.id))
            for dbr in _db_releases:
                if result_item.id == dbr[0]:
                    self.cli.p("Good, first matching record in your collection is:")
                    release_details = self.collection.prepare_release_info(result_item)
                    # we need to pass a list in list here. we use tabulate to view
                    self.cli.tab_online_search_results([release_details])
                    self.cli.online_search_results_tracklist(result_item.tracklist)
                    self.first_track_on_release = result_item.tracklist[0].position
                    break
            try:
                if result_item.id == dbr[0]:
                    #return release_details[0]
                    log.info("Compiled Discogs release_details: {}".format(release_details))
                    return release_details
                # FIXME this is bullshit, will never be reached FIXME
                #    break
            except UnboundLocalError:
                log.error("Discogs collection was not imported to DiscoBASE properly!")
                #raise unb
                raise SystemExit(1)
        return False

    def view_all_releases(self):
        self.cli.p("Showing all releases in DiscoBASE.")
        #all_releases_result = self.cli.trim_table_fields(
        #    self.collection.get_all_db_releases())
        all_releases_result = self.collection.get_all_db_releases()
        self.cli.tab_all_releases(all_releases_result)

    def track_report(self, track_searchterm):
        release = self.search_release(track_searchterm)
        if release:
            track_no = self.cli.ask_for_track(
                suggest=self.cli.first_track_on_release)
            if self.collection.ONLINE == True:
                rel_id = release[0][0]
                rel_name = release[0][2]
            else:
                rel_id = release[0][0]
                rel_name = release[0][1]
            track_occurences = self.collection.track_report_occurences(rel_id, track_no)
            tr_sugg_msg = '\nTrack combo suggestions for {} on "{}".'.format(
                track_no, rel_name)
            tr_sugg_msg+= '\nThis is how you used this track in the past:'
            self.cli.p(tr_sugg_msg)
            if track_occurences:
                for tr in track_occurences:
                    self.cli.p('Snippet of Mix {} - "{}":'.format(
                        tr['mix_id'], tr['name']))
                    report_snippet = self.collection.track_report_snippet(tr['track_pos'], tr['mix_id'])
                    self.cli.tab_mix_table(report_snippet, _verbose = True)
        else:
            raise SystemExit(3)

    # ADD RELEASE TO COLLECTION
    def add_release(self, release_id):
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)
        if not is_number(release_id):
            log.error('Not a number')
            return False
        else:
            # setup.py argparser catches non-int, this is for calls from elsewhere
            if self.collection.search_release_id(release_id):
                msg = "Release ID is already existing in DiscoBASE, "
                msg+= "won't add it to your Discogs collection. We don't want dups!"
                self.cli.p(msg)
            else:
                self.cli.p("Asking Discogs if release ID {:d} is valid.".format(
                       release_id))
                result = self.collection.get_d_release(release_id)
                if result:
                    artists = self.collection.d_artists_to_str(result.artists)
                    d_catno = self.collection.d_get_first_catno(result.labels)
                    log.debug(dir(result))
                    self.cli.p("Adding \"{}\" to collection".format(result.title))
                    for folder in self.collection.me.collection_folders:
                        if folder.id == 1:
                            folder.add_release(release_id)
                            last_row_id = self.collection.create_release(result.id,
                                    result.title, artists, d_catno, d_coll = True)
                    if not last_row_id:
                        self.cli.error_not_the_release()
                    log.debug("Discogs release was maybe added to Collection")
                    self.cli.duration_stats(start_time, 'Adding Release to Collection')
                    return True
                else:
                    log.debug("No Discogs release. Returning False")
                    self.cli.duration_stats(start_time, 'Adding Release to Collection')
                    return False

    # import specific release ID into DB
    def import_release(self, _release_id):
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)
        #print(dir(me.collection_folders[0].releases))
        #print(dir(me))
        #print(me.collection_item)
        #if not force == True:
        self.cli.p("Asking Discogs for release ID {:d}".format(
               _release_id))
        result = self.collection.get_d_release(_release_id)
        if not result:
            raise SystemExit(3)
        else:
            self.cli.p("Release ID is valid: {}\n".format(result.title) +
                  "Let's see if it's in your collection, this might take some time...")
            in_coll = self.collection.is_in_d_coll(_release_id)
            if in_coll:
                artists = self.collection.d_artists_to_str(in_coll.release.artists)
                d_catno = self.collection.d_get_first_catno(in_coll.release.labels)
                self.cli.p(
                  "Found it in collection: {} - {} - {}.\nImporting to DiscoBASE.".format(
                  in_coll.release.id, artists, in_coll.release.title))
                self.collection.create_release(in_coll.release.id, in_coll.release.title,
                  artists, d_catno, d_coll = True)
            else:
                self.cli.error_not_the_release()
        self.cli.duration_stats(start_time, 'Discogs import') # print time stats

    def import_collection(self, tracks = False):
        start_time = time()
        self.cli.exit_if_offline(self.collection.ONLINE)
        self.releases_processed = 0
        self.releases_added = 0
        self.releases_db_errors = 0
        if tracks:
            self.cli.p("Importing Discogs collection into DiscoBASE (extended import - releases and tracks)")
            self.tracks_processed = 0
            self.tracks_added = 0
            self.tracks_db_errors = 0
            self.tracks_discogs_errors = 0
        else:
            self.cli.p("Importing Discogs collection into DiscoBASE (regular import - just releases)")

        for item in self.collection.me.collection_folders[0].releases:
            self.collection.rate_limit_slow_downer(remaining=15, sleep=3)
            d_artists = item.release.artists # we'll need it again with tracks
            artists = self.collection.d_artists_to_str(d_artists)
            first_catno = self.collection.d_get_first_catno(item.release.labels)
            print('Release {} - "{}" - "{}"'.format(item.release.id, artists,
                  item.release.title))
            rel_created = self.collection.create_release(item.release.id,
                  item.release.title, artists, first_catno, d_coll = True)
            # create_release will return False if unsuccessful
            if rel_created:
                self.releases_added += 1
            else:
                self.releases_db_errors += 1
                log.error(
                  'importing release "{}" Continuing anyway.'.format(
                      item.release.title))
            if tracks:
                try:
                    tracklist = item.release.tracklist
                    for track in tracklist:
                        tr_artists = self.collection.d_artists_parse(
                          tracklist, track.position, d_artists)
                        tr_title = track.title
                        if self.collection.upsert_track(item.release.id,
                              track.position, tr_title, tr_artists):
                            self.tracks_added += 1
                            msg_tr_add = 'Track "{}" - "{}"'.format(
                                  tr_artists, tr_title)
                            log.info(msg_tr_add)
                            print(msg_tr_add)
                        else:
                            self.tracks_db_errors += 1
                            log.error(
                              'importing track. Continuing anyway.')
                except Exception as Exc:
                    self.tracks_discogs_errors += 1
                    log.error("Exception: %s", Exc)

            msg_rel_add="Releases so far: {}".format(self.releases_added)
            log.info(msg_rel_add)
            print(msg_rel_add)
            if tracks:
                msg_trk_add="Tracks so far: {}".format(self.tracks_added)
                log.info(msg_trk_add)
                print(msg_trk_add)
            print() # leave space after a release and all its tracks
            self.releases_processed += 1

        print('Processed releases: {}. Imported releases to DiscoBASE: {}.'.format(
            self.releases_processed, self.releases_added))
        print('Database errors (release import): {}.'.format(
            self.releases_db_errors))

        print('Processed tracks: {}. Imported tracks to DiscoBASE: {}.'.format(
            self.tracks_processed, self.tracks_added))
        print('Database errors (track import): {}. Discogs errors (track import): {}.'.format(
            self.tracks_db_errors, self.tracks_discogs_errors))

        self.cli.duration_stats(start_time, 'Discogs import') # print time stats

    def bpm_report(self, bpm, pitch_range):
        #track_no = self.cli.self.cli.ask_for_track()
        #if self.collection.ONLINE == True:
        #    rel_id = release[0][0]
        #    rel_name = release[0][2]
        #else:
        #    rel_id = release[0][0]
        #    rel_name = release[0][1]
        possible_tracks = self.collection.get_tracks_by_bpm(bpm, pitch_range)
        tr_sugg_msg = '\nShowing tracks with a BPM around {}. Pitch range is +/- {}%.'.format(bpm, pitch_range)
        self.cli.p(tr_sugg_msg)
        if possible_tracks:
            max_width = self.cli.get_max_width(possible_tracks,
              ['key', 'bpm'], 3)
            for tr in possible_tracks:
                key_bpm_and_space = self.cli.combine_fields_to_width(tr,
                  ['key', 'bpm'], max_width)
                self.cli.p('{}{} - {} [{} ({})]:'.format(
                     key_bpm_and_space, tr['d_artist'], tr['d_track_name'],
                     tr['discogs_title'], tr['d_track_no']))
                #self.cli.tab_mix_table(report_snippet, _verbose = True)

    def key_report(self, key):
        #if self.collection.ONLINE == True:
        #    rel_id = release[0][0]
        #    rel_name = release[0][2]
        #else:
        #    rel_id = release[0][0]
        #    rel_name = release[0][1]
        possible_tracks = self.collection.get_tracks_by_key(key)
        tr_sugg_msg = '\nShowing tracks with key {}'.format(key)
        self.cli.p(tr_sugg_msg)
        if possible_tracks:
            max_width = self.cli.get_max_width(possible_tracks,
              ['key', 'bpm'], 3)
            for tr in possible_tracks:
                key_bpm_and_space = self.cli.combine_fields_to_width(tr,
                  ['key', 'bpm'], max_width)
                self.cli.p('{}{} - {} [{} ({})]:'.format(
                     key_bpm_and_space, tr['d_artist'], tr['d_track_name'],
                     tr['discogs_title'], tr['d_track_no']))
                #self.cli.tab_mix_table(report_snippet, _verbose = True)

    def update_tracks_from_discogs(self, mixed_tracks):
        '''takes a list of tracks and updates tracknames/artists from Discogs.
           List has to contain fields: d_release_id, discogs_title, d_track_no
        '''
        start_time = time()
        self.tracks_processed = len(mixed_tracks)
        self.tracks_added = 0
        self.tracks_db_errors = 0
        self.tracks_not_found_errors = 0
        for mix_track in mixed_tracks:

            d_track_no = mix_track['d_track_no']
            d_release_id = mix_track['d_release_id']
            discogs_title = mix_track['discogs_title']
            self.collection.rate_limit_slow_downer(remaining=20, sleep=3)

            # move this to method fetch_track_and_artist_from_discogs
            try: # we catch 404 here, and not via get_d_release, to save one request
                name, artist = "", ""
                d_tracklist = self.d.release(d_release_id).tracklist
                name = self.collection.d_tracklist_parse(
                      d_tracklist, d_track_no)
                artist = self.collection.d_artists_parse(
                      d_tracklist, d_track_no,
                      self.d.release(d_release_id).artists)
            except errors.HTTPError as HtErr:
                log.error('Track {} on "{}" ({}) not existing on Discogs ({})'.format(
                      d_track_no, discogs_title, d_release_id, HtErr))
                print("") # space for readability
                continue # jump to next iteration, nothing more to do here

            if name or artist:
                print('Adding Track {} on "{}" ({})'.format(
                      d_track_no, discogs_title, d_release_id))
                print('{} - {}'.format(artist, name))
                if self.collection.upsert_track(d_release_id,
                      d_track_no, name, artist):
                    self.tracks_added += 1
                else:
                    self.tracks_db_errors += 1
                print("") # space for readability
            else:
                print('Either track or artist name not found on "{}" ({}) - Track {} really existing?'.format(
                      discogs_title, d_release_id, d_track_no))
                self.tracks_not_found_errors += 1
                print("") # space for readability

        print('Processed: {}. Added Artist/Track info to DiscoBASE: {}.'.format(
            self.tracks_processed, self.tracks_added))
        print('Database errors: {}. Not found on Discogs errors: {}.'.format(
            self.tracks_db_errors, self.tracks_not_found_errors))
        print("") # space for readability

        self.cli.duration_stats(start_time, 'Updating track info') # print time stats
        return True # we did at least something and thus were successfull

    def update_single_track_from_discogs(self, rel_id, rel_title, track_no):
        if not track_no:
            track_no = self.cli.ask_for_track(suggest = self.first_track_on_release)
        tr_list = [{
              'd_release_id': rel_id,
              'discogs_title': rel_title,
              'd_track_no': track_no
        }]
        return self.update_tracks_from_discogs(tr_list)

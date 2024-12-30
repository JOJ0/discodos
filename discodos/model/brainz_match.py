import logging
# import pprint
import re

from discodos.model import Brainz

log = logging.getLogger('discodos')


class Brainz_match (Brainz):  # we are based on Brainz, but it's not online
    '''This class tries to match _one_ given release and/or recording with
        musicbrainz using the information passed in init'''

    def __init__(self, mb_user, mb_pass, mb_appid,
                 d_release_id, d_release_title, d_catno, d_artist, d_track_name,
                 d_track_no, d_track_no_num, detail=1):
        # FIXME we take mb credentials from passed coll_ctrl object
        super().__init__(mb_user, mb_pass, mb_appid)
        # we don't need to create a Brainz obj, we are a child of it
        # remember all original discogs names
        self.d_release_id_orig = d_release_id
        self.d_release_title_orig = d_release_title
        self.d_catno_orig = d_catno
        self.d_artist_orig = d_artist
        self.d_track_name_orig = d_track_name
        self.d_track_no_orig = d_track_no
        self.d_track_no_num_orig = d_track_no_num
        # self.detail = detail
        # match methods and times init
        self.release_match_method = ''
        self.release_mbid = ''
        self.rec_match_method = ''
        self.rec_mbid = ''
        # strip and lowercase here already, we need it all the time
        self.d_release_id = d_release_id  # no mods here, just streamlining
        self.d_release_title = d_release_title.lower()
        # self.d_catno = d_catno.upper().replace(' ', '') # exp. with upper here
        self.d_catno = d_catno.upper().replace(' ', '')
        if d_artist:
            self.d_artist = d_artist.lower()
        else:  # if it's None or something else
            self.d_artist = ''
        self.d_track_name = d_track_name.lower()
        self.d_track_no = d_track_no.upper()  # upper comparision everywhere
        self.d_track_no_num = int(d_track_no_num)

    def fetch_mb_releases(self, detail):  # fetching controllable from outside
        # decide which search method is used according to detail (-z count)
        # FIXME error handling should be happening here
        if detail < 2:  # be strict, also use _original_ data here
            log.debug('strict catno: {}'.format(self.d_catno_orig))
            log.debug('strict artist: {}'.format(self.d_artist_orig))
            log.debug('strict release: {}'.format(self.d_release_title_orig))
            self.mb_releases = self.search_mb_releases(
                self.d_artist_orig, self.d_release_title_orig,
                self.d_catno_orig, limit=5, strict=True)
        else:  # fuzzy search
            self.mb_releases = self.search_mb_releases(
                self.d_artist, self.d_release_title, self.d_catno,
                limit=5, strict=False
            )
        return True  # FIXME error handling

    def fetch_mb_matched_rel(self, rel_mbid=False):  # mbid passable from outside
        if rel_mbid:  # given from outside, rest of necess. data from init
            self.mb_matched_rel = self.get_mb_release_by_id(rel_mbid)
        else:  # we have it as class attribute already
            self.mb_matched_rel = self.get_mb_release_by_id(self.release_mbid)
        return True  # FIXME error handling

    def match_release(self):  # start a match run (multiple things are tried)
        # first url-match
        self.release_mbid = self.url_match()
        # and then catno-match
        if not self.release_mbid:
            self.release_mbid = self.catno_match()
        # and now try again with some name variation tricks
        # sometimes digital releases have additional D at end or in between
        if not self.release_mbid:
            self.release_mbid = self.catno_match(variations=True)
        # if we still didn't find anything, we have logged already and are
        # returning empty string here
        return self.release_mbid

    def match_recording(self):  # start a match run (multiple things are tried)
        # pprint.pprint(matched_rel) # human readable json
        #  get track position as a number from discogs release
        # print(d_rel.tracklist[index])
        # d_track_position = d_rel.tracklist[index]
        rec_mbid = self.track_name_match()
        if not rec_mbid:
            rec_mbid = self.track_no_match()
        return rec_mbid  # if we didn't find, we logged already and return ''

    # define matching methods as in update_track.... here
    def url_match(self):
        '''finds Release MBID by looking through Discogs links.'''
        # reset match method var. FIXME is this the right place
        self.release_match_method = ''
        for release in self.mb_releases['release-list']:
            log.info('CTRL: ...Discogs-URL-matching MB-Release:')
            log.info('CTRL: ..."{}"'.format(release['title']))
            full_mb_rel = self.get_mb_release_by_id(release['id'])
            # pprint.pprint(full_mb_rel) # DEBUG
            urls = self.get_urls_from_mb_release(full_mb_rel)
            if urls:
                for url in urls:
                    if url['type'] == 'discogs':
                        log.info('CTRL: ...trying Discogs URL: ..{}'.format(
                            url['target'].replace('https://www.discogs.com/', '')))
                        if str(self.d_release_id) in url['target']:
                            log.info("CTRL: Found MusicBrainz match (via "
                                     "Discogs URL)")
                            _mb_rel_id = release['id']
                            self.release_match_method = 'Discogs URL'
                            return _mb_rel_id  # found release match
        return False

    def catno_match(self, variations=False):
        '''finds Release MBID by looking through catalog numbers.'''
        # reset match method var. FIXME is this the right place
        self.release_match_method = ''
        for release in self.mb_releases['release-list']:
            # _mb_rel_id = False # this is what we are looking for
            if variations:
                log.info('CTRL: ...CatNo-matching (variations) MB-Release:')
                log.info('CTRL: ..."{}"'.format(release['title']))
            else:
                log.info('CTRL: ...CatNo-matching (exact) MB-Release:')
                log.info('CTRL: ..."{}"'.format(release['title']))
            full_rel = self.get_mb_release_by_id(release['id'])
            # FIXME should we do something here if full_rel not successful?

            for mb_label_item in full_rel['release']['label-info-list']:
                mb_catno_orig = self.get_catno_from_mb_label(mb_label_item)
                mb_catno = mb_catno_orig.upper().replace(' ', '')
                # log.debug(
                #   'CTRL: ...MB CatNo (upper, no-ws): {}'.format(mb_catno))

                if variations is False:  # this is the vanilla exact-match
                    log.info('CTRL: ...DC CatNo: {}'.format(self.d_catno_orig))
                    log.info('CTRL: ...MB CatNo: {}'.format(mb_catno_orig))
                    if mb_catno == self.d_catno:
                        self.release_match_method = 'CatNo (exact)'
                        self._catno_match_found_msg()
                        return release['id']

                else:  # these are the variation matches
                    # log original DC CatNo only once
                    log.info('CTRL: ...DC CatNo: {}'.format(self.d_catno_orig))

                    # start with simple "ending differences"
                    log.info('CTRL: ...MB CatNo: {} (CD cut off)'.format(mb_catno_orig))
                    mb_catno_last2 = mb_catno[-2:]
                    if mb_catno_last2 == 'CD':
                        mb_catno_cd_cut = mb_catno[:-2]
                        if mb_catno_cd_cut == self.d_catno:
                            self.release_match_method = 'CatNo (var 3)'
                            self.release_mbid = release['id']
                            self._catno_match_found_msg()
                            return self.release_mbid

                    log.info('CTRL: ...MB CatNo: {} (D cut off)'.format(mb_catno_orig))
                    mb_catno_last1 = mb_catno[-1:]
                    if mb_catno_last1 == 'D':
                        mb_catno_d_cut = mb_catno[:-1]
                        if mb_catno_d_cut == self.d_catno:
                            self.release_match_method = 'CatNo (var 1)'
                            self.release_mbid = release['id']
                            self._catno_match_found_msg()
                            return self.release_mbid

                    # now the trickier stuff - char in between is different
                    log.info(
                        'CTRL: ...MB CatNo: {} (middle cut out)'.format(
                            mb_catno_orig)
                    )
                    # FIXME extendable via config.yaml
                    middle_terms = ['-', '#', 'D', 'CD', 'BLACK']
                    if self._catno_has_numtail(mb_catno):
                        for term in middle_terms:
                            log.info('CTRL: ...trying split at: {}'.format(term))
                            parts = self._catno_cutter(mb_catno, term)
                            if parts['term'] == term:
                                mb_catno_d_betw_cut = '{}{}'.format(
                                    parts['before'], parts['after']
                                )
                                if mb_catno_d_betw_cut == self.d_catno:
                                    self.release_match_method = 'CatNo (var 2)'
                                    self.release_mbid = release['id']
                                    self._catno_match_found_msg()
                                    return self.release_mbid

                    # we didn't find a variation and return False
                    log.info('CTRL: ...no applicable variations found')
                    return False

    def _catno_has_numtail(self, catno):
        numtail = re.split('[^\d]', catno)[-1]
        log.debug('CTRL: ...catno_match_numtail return: {}'.format(numtail))
        return numtail

    def _catno_cutter(self, catno, term):
        '''returns 3 parts of catno: before delimiter-term, the delim-term
           and after delim-term, which _has_ to be a number'''
        ret_dict = {}
        # first thing: the tail is a number check, exit if not
        numtail = re.split('[^\d]', catno)[-1]
        if not numtail:
            return False  # should never happen, we catch it with _catno_has_numtail
        # before delimiter-term check
        beforenum = re.split('[^\D]', catno)[0]
        # log.debug('CTRL: ...catno_cutter: beforenum {}'.format(beforenum))
        split_at_term = beforenum.split(term)
        # log.debug('CTRL: ...catno_cutter: split_at_term {}'.format(split_at_term))
        ret_dict['before'] = split_at_term[0]
        ret_dict['term'] = term
        ret_dict['after'] = numtail
        log.debug('CTRL: ...catno_cutter: before: {}'.format(ret_dict['before']))
        # log.debug('CTRL: ...catno_cutter: term: {}'.format(ret_dict['term']))
        log.debug('CTRL: ...catno_cutter: after: {}'.format(ret_dict['after']))
        return ret_dict

    def _catno_match_found_msg(self):
        # only show this final log line if we found a match
        log.info('CTRL: Found MusicBrainz release match via {} '.format(
                 self.release_match_method))

    def track_name_match(self):
        # pprint.pprint(_mb_release) # human readable json
        self.rec_match_method = ''
        for medium in self.mb_matched_rel['release']['medium-list']:
            for track in medium['track-list']:
                _rec_title = track['recording']['title']
                _rec_title_low = _rec_title.lower()  # we made discogs lower too
                if _rec_title_low == self.d_track_name:
                    self.rec_mbid = track['recording']['id']
                    log.info('CTRL: Track name matches: {}'.format(
                        _rec_title))
                    log.info('CTRL: Recording MBID: {}'.format(
                        self.rec_mbid))  # finally we have a rec MBID
                    self.rec_match_method = 'Track Name'
                    return self.rec_mbid
        log.info('CTRL: No track name match: {} vs. {}'.format(
            self.d_track_name_orig, _rec_title))
        return False

    def track_no_match(self):
        # pprint.pprint(_mb_release) # human readable json
        self.rec_match_method = ''
        for medium in self.mb_matched_rel['release']['medium-list']:
            # track_count = len(medium['track-list'])
            for track in medium['track-list']:
                _rec_title = track['recording']['title']
                track_number = track['number'].upper(),  # could be A, AA, a, ..
                track_position = int(track['position'])  # starts at 1, ensure int
                if track_number == self.d_track_no:
                    self.rec_mbid = track['recording']['id']
                    log.info('CTRL: Track number matches: {}'.format(
                        _rec_title))
                    log.info('CTRL: Recording MBID: {}'.format(
                        self.rec_mbid))  # finally we have a rec MBID
                    self.rec_match_method = 'Track No'
                    return self.rec_mbid
                elif track_position == self.d_track_no_num:
                    self.rec_mbid = track['recording']['id']
                    log.info('CTRL: Track number "numerical" matches: {}'.format(
                        _rec_title))
                    log.info('CTRL: Recording MBID: {}'.format(
                        self.rec_mbid))  # finally we have a rec MBID
                    self.rec_match_method = 'Track No (num)'
                    return self.rec_mbid
        log.info('CTRL: No track number or numerical position match: {} vs. {}'.format(
            self.d_track_no_num, track_position))
        return False

import logging
# import pprint
import json
import requests
import requests.exceptions
import musicbrainzngs as m
from musicbrainzngs import WebServiceError

log = logging.getLogger('discodos')


class Brainz (object):

    def __init__(self, musicbrainz_user, musicbrainz_pass, musicbrainz_appid):
        self.ONLINE = False
        self.musicbrainz_user = musicbrainz_user
        self.musicbrainz_password = musicbrainz_pass
        self.musicbrainz_appid = musicbrainz_appid
        if self.musicbrainz_connect(musicbrainz_user, musicbrainz_pass, musicbrainz_appid):
            self.ONLINE = True
            log.debug("MODEL: Brainz class is ONLINE.")

    # musicbrainz connect try,except wrapper
    def musicbrainz_connect(self, mb_user, mb_pass, mb_appid):
        # If you plan to submit data, authenticate
        m.auth(mb_user, mb_pass)
        m.set_useragent(mb_appid[0], mb_appid[1])  # 0=version, 1=app
        # If you are connecting to a different server
        # m.set_hostname("beta.musicbrainz.org")
        # m.set_rate_limit(limit_or_interval=1.0, new_requests=1)
        try:  # test request
            m.get_artist_by_id("952a4205-023d-4235-897c-6fdb6f58dfaa", [])
            self.ONLINE = True
            return True
        except WebServiceError as exc:
            log.error("connecting to MusicBrainz: %s" % exc)
            self.ONLINE = False
            return False

    def get_mb_artist_by_id(self, mb_id):
        try:
            return m.get_artist_by_id(mb_id, [])
        except WebServiceError as exc:
            log.error("requesting data from MusicBrainz: %s (WebServiceError)" % exc)
            log.debug("MODELS: get_mb_artist_by_id returns False.")
            return False
        except Exception as exc:
            log.error("requesting data from MusicBrainz: %s (Exception)" % exc)
            log.debug("MODELS: get_mb_artist_by_id returns empty dict.")
            return {}

    def search_mb_releases(self, artist, album, cat_no=False,
                           limit=10, strict=False):
        try:
            if cat_no:
                return m.search_releases(
                    artist=artist, release=album,
                    catno=cat_no, limit=limit, strict=strict
                )
            else:
                return m.search_releases(
                    artist=artist, release=album,
                    limit=limit, strict=strict
                )
        except WebServiceError as exc:
            log.error(
                "requesting data from MusicBrainz: %s (WebServiceError)" % exc
            )
            log.debug("MODELS: search_mb_releases returns False.")
            return False
        except Exception as exc:
            log.error("requesting data from MusicBrainz: %s (Exception)" % exc)
            log.debug("MODELS: search_mb_releases returns empty dict.")
            return {}

    def get_mb_release_by_id(self, mb_id):
        try:
            return m.get_release_by_id(
                mb_id, includes=[
                    "release-groups",
                    "artists", "labels", "url-rels", "recordings",
                    "recording-rels", "recording-level-rels"
                ]
            )
        except WebServiceError as websvcerr:
            log.error("requesting data from MusicBrainz: %s (WebServiceError)" % websvcerr)
            log.debug("MODELS: get_mb_release_by_id returns empty dict.")
            return {}
        except Exception as exc:
            log.error("requesting data from MusicBrainz: %s (Exception)" % exc)
            log.debug("MODELS: get_mb_release_by_id returns empty dict.")
            return {}

    def get_mb_recording_by_id(self, mb_id):
        try:
            return m.get_recording_by_id(
                mb_id, includes=["url-rels"]
            )
        except WebServiceError as exc:
            log.error("requesting data from MusicBrainz: %s (WebServiceError)" % exc)
            log.debug("MODELS: get_mb_recording_by_id returns False.")
            return False
        except Exception as exc:
            log.error("requesting data from MusicBrainz: %s (Exception)" % exc)
            log.debug("MODELS: get_mb_recording_by_id returns empty dict.")
            return {}

    def get_urls_from_mb_release(self, full_rel):  # takes what get_mb_release_by_id returned
        # log.debug(full_rel['release'].keys())
        if 'url-relation-list' in full_rel['release']:
            return full_rel['release']['url-relation-list']
        else:
            return []

    def get_catno_from_mb_label(self, mb_label):  # label-info-list item
        # log.debug(mb_label)
        if 'catalog-number' in mb_label:
            return mb_label['catalog-number']
        else:
            return ''

    def _get_accousticbrainz(self, urlpart):
        headers={'Accept': 'application/json'}
        url="https://acousticbrainz.org/api/v1/{}".format(urlpart)
        try:
            resp = requests.get(url, headers=headers, timeout=7)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            log.debug("fetching AcousticBrainz MBID: %s (HTTPError)", errh)
            if "Not found" in errh.response.text:
                log.warning("AcousticBrainz missing recording. Consider submitting it!")
            return None
        except requests.exceptions.ConnectionError as errc:
            log.error("fetching AcousticBrainz MBID: %s (ConnectionError)", errc)
            return None
        except requests.exceptions.Timeout as errt:
            log.error("fetching AcousticBrainz MBID: %s (Timeout)", errt)
            return None
        except requests.exceptions.RequestException as erre:
            log.error("fetching AcousticBrainz MBID: %s (RequestException)", erre)
            return None

        if resp.ok:
            _json = json.loads(resp.content)
            return _json
        else:
            log.debug("No valid AcousticBrainz response. Returning None.")
            return None

    def _get_accbr_low_level(self, mb_id):
        low_level = self._get_accousticbrainz("{}/low-level".format(mb_id))
        # pprint.pprint(low_level)
        return low_level

    def _get_accbr_high_level(self, mb_id):
        return self._get_accousticbrainz("{}/high-level".format(mb_id))

    # def _get_accbr_url_rels(self, )

    def get_accbr_bpm(self, mb_id):
        try:
            ab_return = self._get_accbr_low_level(mb_id)
            return ab_return['rhythm']['bpm']
        except:
            return None

    def get_accbr_key(self, mb_id):
        try:
            ab_return = self._get_accbr_low_level(mb_id)
            if ab_return['tonal']['key_scale'] == 'minor':
                majmin = 'm'
            else:
                majmin = ''
            key_key = '{}{}'.format(ab_return['tonal']['key_key'], majmin)
            return key_key
        except:
            return None

    def get_accbr_chords_key(self, mb_id):
        try:
            ab_return = self._get_accbr_low_level(mb_id)
            if ab_return['tonal']['chords_scale'] == 'minor':
                majmin = 'm'
            else:
                majmin = ''
            chords_key = '{}{}'.format(ab_return['tonal']['chords_key'], majmin)
            return chords_key
        except:
            return None

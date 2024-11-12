import time
import logging
from socket import gaierror
import discogs_client
import discogs_client.exceptions
from discogs_client import Condition, Status
import requests.exceptions
import urllib3.exceptions

from discodos.utils import is_number

log = logging.getLogger('discodos')

CONDITIONS = {
    "M": Condition.MINT,
    "NM": Condition.NEAR_MINT,
    "VG+": Condition.VERY_GOOD_PLUS,
    "VG": Condition.VERY_GOOD,
    "G+": Condition.GOOD_PLUS,
    "G": Condition.GOOD,
    "F": Condition.FAIR,
}
STATUS = {
    "For Sale": Status.FOR_SALE,
    "Draft": Status.DRAFT,
}

class DiscogsMixin:
    """Discogs connection, fetchers and helpers."""
    def discogs_connect(self, user_token=None, app_identifier=None,
                        discogs=None):
        """Discogs connect try,except wrapper sets attributes d, me and ONLINE.
        """
        try:
            if discogs:
                self.d = discogs
                self.me = discogs.identity()
                self.ONLINE = True
                return self.ONLINE

            self.d = discogs_client.Client(
                app_identifier, user_token=user_token
            )
            self.me = self.d.identity()
            self.ONLINE = True
        except Exception:  # pylint: disable=broad-exception-caught
            self.ONLINE = False

        return self.ONLINE

    # Actual online fetchers

    def search_release_online(self, id_or_title):
        try:
            if is_number(id_or_title):
                releases = [self.d.release(id_or_title)]
            else:
                releases = self.d.search(id_or_title, type='release')
            # exceptions are only triggerd if trying to access the release obj
            if len(releases) > 0:  # fixes list index error
                log.info("First found release: {}".format(releases[0]))
            log.debug("All found releases: {}".format(releases))
            return releases
        except discogs_client.exceptions.HTTPError as HtErr:
            log.error("%s (HTTPError)", HtErr)
        except urllib3.exceptions.NewConnectionError as ConnErr:
            log.error("%s (NewConnectionError)", ConnErr)
        except urllib3.exceptions.MaxRetryError as RetryErr:
            log.error("%s (MaxRetryError)", RetryErr)
        except requests.exceptions.ConnectionError as ConnErr:
            log.error("%s (ConnectionError)", ConnErr)
        except gaierror as GaiErr:
            log.error("%s (socket.gaierror)", GaiErr)
        except TypeError as TypeErr:
            log.error("%s (TypeError)", TypeErr)
        except Exception as Exc:
            log.error("%s (Exception)", Exc)
            raise Exc
        return None

    def prepare_release_info(self, release):
        """Takes a discogs_client Release object and returns the relevant data
        as a dictionary. We use it for a nicely formatted release view using
        tabulate"""
        rel_details={}
        rel_details['id'] = release.id
        rel_details['artist'] = release.artists[0].name
        rel_details['title'] = release.title
        if len(release.labels) != 0:
            rel_details['label'] = release.labels[0].name
        rel_details['country'] = release.country
        rel_details['year'] = release.year
        rel_details['format'] = release.formats[0]['descriptions'][0]
        if len(release.formats[0]['descriptions']) > 1:
            rel_details['format'] += ' {}'.format(
                release.formats[0]['descriptions'][1]
            )

        log.info("prepare_release_info: rel_details: {}".format(
            rel_details))
        return rel_details

    def prepare_tracklist_info(self, release_id, tracklist):
        """Takes a tracklist (list) we received from a Discogs release object
        and augments it with additional DiscoBASE data"""
        tl=[]
        for track in tracklist:
            dbtrack = self.get_track(release_id, track.position)
            if dbtrack is None:
                log.debug("MODEL: prepare_tracklist_info: Track not in DB. "
                          "Adding title/track_no only.")
                tl.append({
                    'track_no': track.position,
                    'track_title': track.title
                })
            else:
                tl.append({
                    'track_no': track.position,
                    'track_title': track.title,
                    'key': dbtrack['key'],
                    'key_notes': dbtrack['key_notes'],
                    'bpm': dbtrack['bpm'],
                    'notes': dbtrack['notes'],
                    'a_key': dbtrack['a_key'],
                    'a_chords_key': dbtrack['a_chords_key'],
                    'a_bpm': dbtrack['a_bpm']
                })
        return tl

    def get_d_release(self, release_id, catch=True):
        try:
            r = self.d.release(release_id)
            if catch is True:
                log.debug(
                    "Proactively accessing Release object to catch errors: %s",
                    r.title,
                )
            return r
        except discogs_client.exceptions.HTTPError as HtErr:
            log.error('Release not existing on Discogs ({})'.format(HtErr))
            return False
        except urllib3.exceptions.NewConnectionError as ConnErr:
            log.error("%s", ConnErr)
            return False
        except urllib3.exceptions.MaxRetryError as RetryErr:
            log.error("%s", RetryErr)
            return False
        except Exception as Exc:
            log.error("Exception: %s", Exc)
            return False

    def release_from_collection(self, release_id):
        release_instances = self.me.collection_items(release_id)
        if not release_instances:
            return None
        for count, instance in enumerate(release_instances, start=1):
            if count > 0:
                log.debug(
                    "MODEL: Multiple instances of %s %s in collection: %s",
                    release_id, instance.release.title, count
                )
            release = instance.release
        return release

    def stats_releases_d_collection_online(self):
        count = 0
        try:
            count = len(self.me.collection_folders[0].releases)
        except Exception as Exc:
            log.error("%s (Exception)", Exc)
        return count

    def fetch_sales_listing_details(self, listing_id):
        """Fetches details like price for a Discogs marketplace listing."""
        listing = self.d.listing(listing_id)
        l = {
            "d_sales_release_id": listing.release.id,
            "d_sales_release_url": listing.release.url,
            "d_sales_url": listing.url,
            "d_sales_condition": listing.condition,
            "d_sales_sleeve_condition": listing.sleeve_condition,
            "d_sales_price": str(listing.price.value),
            "d_sales_comments": listing.comments,
            "d_sales_allow_offers": listing.allow_offers,
            "d_sales_status": listing.status,
            "d_sales_comments_private": listing.external_id,
            "d_sales_counts_as": str(listing.format_quantity),
            "d_sales_location": listing.location,
            "d_sales_weight": str(listing.weight),
            "d_sales_posted": listing.posted,
        }
        return l if l else None

    def fetch_marketplace_stats(self, release_id):
        release = self.d.release(release_id)
        r = {
            "lowest_price": str(release.marketplace_stats.lowest_price.value),
            "num_for_sale": str(release.marketplace_stats.num_for_sale),
            "blocked_from_sale": str(release.marketplace_stats.blocked_from_sale),
        }
        return r if r else None

    def fetch_price_suggestion(self, release_id, condition):
        release = self.d.release(release_id)
        r = {
            "M": release.price_suggestions.mint,
            "VG+": release.price_suggestions.very_good_plus,
            "VG": release.price_suggestions.very_good,
            "G+": release.price_suggestions.good_plus,
            "G": release.price_suggestions.good,
            "F": release.price_suggestions.fair,
        }
        return r[condition.upper()] if r else None

    def list_for_sale(  # pylint: disable=too-many-positional-arguments,too-many-arguments
        self,
        release_id=None,
        condition=None,
        sleeve_condition=None,
        price=None,
        status=None,
        location=None,
        allow_offers=None,
        comments=None,
        private_comments=None,
    ):
        """Lists a record for sale."""
        try:
            self.me.inventory.add_listing(
                release_id,
                CONDITIONS[condition],
                price,
                STATUS[status],
                sleeve_condition=CONDITIONS[sleeve_condition],
                comments=comments,
                allow_offers="true" if allow_offers else "false",
                external_id=private_comments,
                location=location,
                # weight=None,
                # format_quantity=None,
            )
            return True
        except Exception as Exc:
            log.error("Exception while trying to list for sale: %s", Exc)
            return False

    def rate_limit_slow_downer(self, remaining=10, sleep=2):
        '''Discogs util: stay in 60/min rate limit'''
        if int(self.d._fetcher.rate_limit_remaining) < remaining:  # pylint: disable=protected-access
            log.info(
                "Discogs request rate limit is about to exceed, "
                "let's wait a little: %s",
                self.d._fetcher.rate_limit_remaining  # pylint: disable=protected-access
            )
            # while int(self.d._fetcher.rate_limit_remaining) < remaining:
            time.sleep(sleep)
        else:
            log.info(
                "Discogs rate limit: %s remaining.",
                self.d._fetcher.rate_limit_remaining  # pylint: disable=protected-access
            )

    # Discogs data helpers

    def d_artists_to_str(self, d_artists):
        '''gets a combined string from discogs artistlist object'''
        artist_str=''
        for cnt, artist in enumerate(d_artists):
            if cnt == 0:
                artist_str = artist.name
            else:
                artist_str += ' / {}'.format(artist.name)
        log.info('MODEL: combined artistlist to string \"{}\"'.format(artist_str))
        return artist_str

    def d_artists_parse(self, d_tracklist, track_number, d_artists):
        '''gets Artist name from discogs release (child)objects via track_number, eg. A1
           params d_artist: FIXME'''
        for tr in d_tracklist:
            # log.debug("d_artists_parse: this is the tr object: {}".format(dir(tr)))
            # log.debug("d_artists_parse: this is the tr object: {}".format(tr))
            if tr.position.upper() == track_number.upper():
                # log.info("d_tracklist_parse: found by track number.")

                if len(tr.artists) == 1:
                    name = tr.artists[0].name
                    log.info(
                        f"MODEL: d_artists_parse: just one artist, returning it: {name}"
                    )
                    return name

                if len(tr.artists) == 0:
                    log.info(
                        "MODEL: d_artists_parse: no artists in tracklist, "
                        "checking d_artists object..")
                    combined_name = self.d_artists_to_str(d_artists)
                    return combined_name

                log.info("tr.artists len: {len(tr.artists)}")
                for a in tr.artists:
                    log.debug(f"release.artists debug loop: {a.name}")
                combined_name = self.d_artists_to_str(tr.artists)
                log.info(
                    "MODEL: d_artists_parse: several artists, "
                    f"returning combined named {combined_name}")
                return combined_name

        log.debug('d_artists_parse: Track {track_number} not existing on release.')
        return None

    def d_tracklist_parse(self, d_tracklist, track_number):
        '''gets Track name from discogs tracklist object via track_number, eg. A1'''
        for tr in d_tracklist:
            # log.debug("d_tracklist_parse: this is the tr object: {}".format(dir(tr)))
            # log.debug("d_tracklist_parse: this is the tr object: {}".format(tr))
            if (track_number is not None
                    and tr.position.upper() == track_number.upper()):
                return tr.title
        log.debug(
            'd_tracklist_parse: Track {} not existing on release.'.format(
                track_number)
        )
        return False  # we didn't find the tracknumber

    def d_tracklist_parse_numerical(self, d_tracklist, track_number):
        '''get numerical track pos from discogs tracklist object via
           track_number, eg. A1'''
        for num, tr in enumerate(d_tracklist):
            if tr.position.lower() == track_number.lower():
                return num + 1  # return human readable (matches brainz position)
        log.debug("d_tracklist_parse_numerical: "
                  "Track {} not existing on release.".format(track_number))
        return False  # we didn't find the tracknumber

    def d_get_first_catno(self, d_labels):
        '''get first found catalog number from discogs label object'''
        catno_str = ''
        if len(d_labels) == 0:
            log.warning(
                "MODEL: Discogs release without Label/CatNo. This is weird!"
            )
        else:
            for cnt, label in enumerate(d_labels):
                if cnt == 0:
                    catno_str = label.data['catno']
                else:
                    log.info(
                        'MODEL: Found multiple CatNos, not adding "%s"',
                        label.data['catno']
                    )
            log.info('MODEL: Found Discogs CatNo "%s"', catno_str)
        return catno_str

    def d_get_all_catnos(self, d_labels):
        '''get all found catalog number from discogs label object concatinated
           with newline'''
        catno_str = ''
        if len(d_labels) == 0:
            log.warning("MODEL: Discogs release without Label/CatNo. "
                        "This is weird!")
        else:
            for cnt, label in enumerate(d_labels):
                if cnt == 0:
                    catno_str = label.data['catno']
                else:
                    catno_str += '\n{}'.format(label.data['catno'])
            log.info('MODEL: Found Discogs CatNo(s) "{}"'.format(catno_str))
        return catno_str
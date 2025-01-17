import logging
from tabulate import tabulate as tab
# from textual.css import StyleSheet
from rich import print  # pylint: disable=redefined-builtin

from discodos.view import ViewCommon, ViewCommonCommandline

log = logging.getLogger('discodos')

class CollectionViewCommon():
    """Collection view utils, usable in CLI and GUI, related to Collection only

    Lists of questions. Used in CLI:
        self._edit_track_questions: when editing a collection-track.
    """
    def __init__(self):
        super().__init__()
        # List of questions a user is asked when searching and editing a track.
        # First list item is the related db-field, second is the question
        self._edit_track_questions = [
            ["key", "Key ({}): "],
            ["bpm", "BPM ({}): "],
            ["key_notes", "Key notes/bassline/etc. ({}): "],
            ["notes", "Other track notes: ({}): "],
            ["m_rec_id_override", "Override MusicBrainz Recording ID: ({}): "]
        ]


class CollectionViewCommandline(
    CollectionViewCommon, ViewCommonCommandline, ViewCommon
):
    """ Viewing collection (search) outputs on CLI.
    """
    def __init__(self):
        super(CollectionViewCommandline, self).__init__()

    # Format helpers

    def online_search_results_tracklist(self, _tracklist):
        for tr in _tracklist:
            try:
                # concatenate key and bpm together if existing:
                key_bpm_user = "("
                if tr['key']:
                    key_bpm_user+= tr['key']

                if tr['key'] and tr['bpm']:
                    key_bpm_user+= "/" + str(tr['bpm'])
                elif tr['bpm']:
                    key_bpm_user+= str(tr['bpm'])
                key_bpm_user += ")"
                if key_bpm_user == "()":  # if empty, remove it completely
                    key_bpm_user = ""

                # do the same for brainz values:
                key_bpm_brainz = "("
                if tr['a_key']:
                    key_bpm_brainz+= tr['a_key'] + '*'

                if tr['a_key'] and tr['a_bpm']:
                    bpm_rnd = str(round(float(tr['a_bpm']), 1))
                    key_bpm_brainz+= '/{}*'.format(bpm_rnd)
                elif tr['a_bpm']:
                    bpm_rnd = str(round(float(tr['a_bpm']), 1))
                    key_bpm_brainz+= '{}*'.format(bpm_rnd)
                key_bpm_brainz += ')'
                if key_bpm_brainz == '()':  # if empty, remove it completely
                    key_bpm_brainz = ''

                # the final tracklist entry:
                print("{}\t{} {} {}".format(tr['track_no'], tr['track_title'],
                      key_bpm_user, key_bpm_brainz))
            except KeyError:
                # the final tracklist entry if track details not yet in DB:
                print("{}\t{}".format(tr['track_no'], tr['track_title']))
        print('')

    # Tabulate formatters

    def tab_online_search_results(self, _result_list):
        self.p(
            tab(
                _result_list,
                tablefmt="simple",
                headers={
                    "id": "ID",
                    "artist": "Artist",
                    "title": "Release",
                    "label": "Label",
                    "country": "C",
                    "year": "Year",
                    "format": "Format",
                },
            ),
            _log=None,
        )

    def tab_ls_releases(self, _result_list):
        self.p(
            tab(
                _result_list,
                tablefmt="simple",
                headers = self.cols_key_value_search.headers_dict()
            ),
            _log=None
        )

    def tab_all_releases(self, releases_data):
        table = [dict(row) for row in releases_data]
        for i, row in enumerate(table):
            links_str = self.join_links_to_str(row)
            row['artist_title_links'] = '{} - {}\n{}\n '.format(
                row['d_artist'],
                row['discogs_title'],
                links_str
            )
            del table[i]['m_rel_id_override']
            del table[i]['m_rel_id']
            del table[i]['discogs_id']
            del table[i]['d_artist']
            del table[i]['discogs_title']
            del table[i]['d_sales_listing_id']
        table = self.trim_table_fields(table, 40)
        print(tab(table, tablefmt="grid", headers={
            'd_catno': 'CatNo',
            'artist_title_links': 'Release: Artist - Title - Links'
        }))

    def tab_stats(
        self, releases_total, releases_matched,
        tracks_total, tracks_matched,
        collection_items_discobase, collection_items_discogs,
        sales_listings_discobase, sales_listings_discogs,
        sales_listings_forsale,
        sales_listings_sold,
        mixtracks_total, mixtracks_unique,
        tracks_key_brainz, tracks_key_manual,
        tracks_bpm_brainz, tracks_bpm_manual
    ):
        stats = [
            ['Releases in DiscoBASE', releases_total],
            ['Collection items (DiscoBASE)', collection_items_discobase],
            ['Collection items (Discogs)', collection_items_discogs],
            ['Sales listings (DiscoBASE)', sales_listings_discobase],
            ['Sales listings (Discogs)', sales_listings_discogs],
            ['Sales listings (For Sale/Expired)', sales_listings_forsale],
            ['Sales listings (Sold)', sales_listings_sold],
            ['Releases matched with *Brainz', releases_matched],
            ['Tracks in DiscoBASE', tracks_total],
            ['Tracks matched with *Brainz', tracks_matched],
            ['Tracks with *Brainz key', tracks_key_brainz],
            ['Tracks with *Brainz BPM', tracks_bpm_brainz],
            ['Tracks with user-provided key', tracks_key_manual],
            ['Tracks with user-provided BPM', tracks_bpm_manual],
            ['Tracks in mixes', mixtracks_total],
            ['Unique tracks in mixes', mixtracks_unique],
        ]
        self.p(tab(stats, tablefmt='plain'), lead_nl=True, _log=None)

    # Error displays

    def error_not_the_release(self):
        log.error("This is not the release you are looking for!")
        print(r'''
                                     .=.
                                    '==c|
                                    [)-+|
                                    //'_|
                               snd /]==;\
              ''')

    def exit_if_offline(self, online):
        if not online:
            log.error("Need to be ONLINE to do that!")
            raise SystemExit(3)

    # Reports & status updates

    def brainz_processed_report(
        self, processed, added_release, added_rec, added_key, added_chords_key,
        added_bpm, errors_db, errors_not_found, errors_no_rec_AB,
        errors_not_imported, warns_discogs_fetches
    ):
        msg_mb = 'Processed: {}.\nMusicBrainz info added to DiscoBASE: '.format(processed)
        msg_mb+= 'Release MBIDs: {}, Recording MBIDs: {}\n'.format(
            added_release, added_rec)
        msg_mb+= 'AccousticBrainz info added: Key: {}, Chords Key: {}, BPM: {}\n'.format(
            added_key, added_chords_key, added_bpm)
        msg_mb+= 'No AcousticBrainz entries available yet: {}'.format(errors_no_rec_AB)

        msg_err = 'Database errors: {}. Not found on Discogs errors: {}. '.format(
            errors_db, errors_not_found)
        msg_err+= 'No track number in DiscoBASE errors: {}.\n'.format(errors_not_imported)
        msg_err+= 'Additional Discogs fetches necessary: {}.'.format(warns_discogs_fetches)

        msg_note = 'Note: '
        msg_note+= 'Some of the processed tracks might be on the same release. '
        msg_note+= 'Thus, the total "Release MBID count" added in reality might be less.\n\n'
        msg_note+= 'Note: Many "Additional Discogs fetches" or '
        msg_note+= '"No track number in DiscoBASE errors"?\n'
        msg_note+= '-> Improve by pre-filling the DiscoBASE with '
        msg_note+= 'track info (disco import -u)\n\n'
        msg_note+= 'Note: Many missing AcoustingBrainz entries?\n'
        msg_note+= '-> Consider submitting audio recordings to AcousticBrainz: \n'
        msg_note+= '   https://musicbrainz.org/doc/How_to_Submit_Analyses_to_AcousticBrainz'
        print(msg_mb + '\n' + msg_err + '\n\n' + msg_note)
        log.info(msg_mb + '\n' + msg_err +'\n\n' + msg_note)
        print("")  # space for readability

        msg1 = "Note: Not many Release MBIDs or Recording MBIDs found at all?\n"
        msg1+= "-> Please help improving the matching algorithm and either:"
        print(msg1 + '\n')

        msg2 = "* Investigate yourself: Execute match command again with increased log-level: disco -v ...\n"
        msg2+= "* or just send the debug.log file (it's in your discodos config/data folder)\n"
        msg2+= "In any case, please report by opening an issue on github.com/JOJ0/discodos"
        print(msg2 + '\n')

    def brainz_processed_so_far(self, processed, processed_total):
        msg_proc='{}/{}'.format(processed, processed_total)
        log.info(msg_proc)
        print(msg_proc)

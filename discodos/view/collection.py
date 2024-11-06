import logging
import asyncio
from tabulate import tabulate as tab
from textual.app import App
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    Static,
)


from discodos.view import ViewCommon, ViewCommonCommandline
from discodos.model_collection import DiscogsMixin

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


class DiscodosListApp(App, DiscogsMixin):
    """Inline Textual app to view and edit dsc ls results."""
    CSS_PATH = "tui_ls.tcss"
    BINDINGS = [
        ("m", "toggle_dark", "Toggle dark mode"),
        ("q", "request_quit", "Quit"),
        ("l", "list_sale", "List for sale"),
        ("d", "draft_sale", "Set to draft"),
        ("e", "edit_release", "Edit release"),
        ("E", "edit_sale", "Edit sales listing"),
    ]
    def __init__(self, rows, headers, discogs=None):
        super().__init__()
        super().discogs_connect(
            user_token=None,
            app_identifier=None,
            discogs=discogs,
        )
        self.rows = rows
        self.headers = headers
        self.details_panel = None

    def compose(self):
        table = DataTable(classes="ls_results-list")
        table.focus()
        table.add_columns(*self.headers)
        table.cursor_type = "cell"
        table.zebra_stripes = True
        self.details_panel = Label("Hit enter on a cell to view details here!")
        yield Horizontal(table, self.details_panel)
        yield table
        yield Footer()

    def action_toggle_dark(self):
        self.dark = not self.dark

    def action_request_quit(self):
        self.exit()

    def action_list_sale(self):
        pass

    def action_draft_sale(self):
        pass

    def action_edit_release(self):
        pass

    def action_edit_sale(self):
        pass

    def on_mount(self):
        self.title = "DiscoDOS ls results"
        self.sub_title = "Use keystrokes to edit/sell/view details, ..."
        self._load_ls_results()

    def on_data_table_cell_selected(self, event):
        log.debug(event.coordinate)
        if event.coordinate.column != 4 or event.value is None:
            return
        result = self.get_sales_listing_details(event.value)
        self.details_panel.update(result)

    def _load_ls_results(self):
        table_widget = self.query_one(DataTable)
        for row in self.rows:
            row_id, *row_data = row
            table_widget.add_row(*row_data, key=row_id)


class CollectionViewCommandline(
    CollectionViewCommon, ViewCommonCommandline, ViewCommon
):
    """ Viewing collection (search) outputs on CLI.
    """
    def __init__(self):
        super(CollectionViewCommandline, self).__init__()

    def tab_online_search_results(self, _result_list):
        self.p(
            tab(_result_list, tablefmt="simple", headers={
                'id': 'ID', 'artist': 'Artist', 'title': 'Release',
                'label': 'Label', 'country': 'C', 'year': 'Year',
                'format': 'Format'
            }))

    def tab_ls_releases(self, _result_list):
        self.p(
            tab(
                _result_list,
                tablefmt="simple",
                headers=["ID", "Cat. #", "Artist", "Title", "D. Coll.", "For Sale"],
            )
        )

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

    def tab_all_releases(self, releases_data):
        table = [dict(row) for row in releases_data]
        for i, row in enumerate(table):
            links_str = self.join_links_to_str(row)
            row['artist_title_links'] = '{} - {}\n{}\n '.format(
                row['d_artist'],
                row['discogs_title'],
                links_str
            )
            del(table[i]['m_rel_id_override'])
            del(table[i]['m_rel_id'])
            del(table[i]['discogs_id'])
            del(table[i]['d_artist'])
            del(table[i]['discogs_title'])
        table = self.trim_table_fields(table, 40)
        print(tab(table, tablefmt="grid", headers={
            'd_catno': 'CatNo',
            'artist_title_links': 'Release: Artist - Title - Links'
        }))

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

    def tab_stats(
        self, releases_total, releases_matched,
        tracks_total, tracks_matched,
        releases_collection_flag, releases_collection_online,
        mixtracks_total, mixtracks_unique,
        tracks_key_brainz, tracks_key_manual,
        tracks_bpm_brainz, tracks_bpm_manual
    ):
        stats = [
            ['Releases in DiscoBASE', releases_total],
            ['Releases in Collection (DB flag)', releases_collection_flag],
            ['Releases in Collection (Discogs)', releases_collection_online],
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
        self.p(tab(stats, tablefmt='plain'), lead_nl=True)

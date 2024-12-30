import logging
from tabulate import tabulate as tab

from discodos.view import ViewCommon
from discodos.view import ViewCommonCommandline

log = logging.getLogger('discodos')

class MixViewCommon(ViewCommonCommandline):
    ''' Constants and utils used for viewing Mixes. Usable in CLI and GUI.

    Lists of questions. Used in CLI:
        self._edit_track_questions: when editing a mix-track.
        self._edit_mix_questions: when editing a mixes info.
    '''
    def __init__(self):
        super().__init__()
        # Edit questions
        self._edit_track_questions = [
            ["key", "Key ({}): "],
            ["bpm", "BPM ({}): "],
            ["d_track_no", "Track # on record ({}): "],
            ["track_pos", "Move track's position ({}): "],
            ["key_notes", "Key notes/bassline/etc. ({}): "],
            ["trans_rating", "Transition rating ({}): "],
            ["trans_notes", "Transition notes ({}): "],
            ["notes", "Other track notes: ({}): "],
            ["m_rec_id_override", "Override MusicBrainz Recording ID: ({}): "]
        ]
        self._edit_mix_questions = [
            ["name", "Name ({}): "],
            ["played", "Played ({}): "],
            ["venue", "Venue ({}): "]
        ]

    def shorten_mixes_timestamps(self, mixes):
        ''' Reformats timestamps in a list of mixes.

        Argument mixes, usually an sqlite tuples list, will be translated into
        a list of mutable dicts. If it's one already, it's done anyway.
        '''
        mixes = [dict(row) for row in mixes]
        for i, mix in enumerate(mixes):
            mixes[i]['created'] = self.shorten_timestamp(
                mix['created'],
                text=True
            )
            mixes[i]['played'] = self.format_date_month(
                mix['played'],
                text=True
            )
            mixes[i]['updated'] = self.shorten_timestamp(
                mix['updated'],
                text=True
            )
        return mixes


class MixViewCommandline(MixViewCommon, ViewCommonCommandline, ViewCommon):
    """ Viewing mixes outputs on CLI.
    """
    def __init__(self):  # pylint: disable=useless-parent-delegation
        super().__init__()

    def tab_mixes_list(self, mixes_data):
        mixes_short_timestamps = self.shorten_mixes_timestamps(mixes_data)
        tabulated = tab(
            self.trim_table_fields(mixes_short_timestamps),
            tablefmt="simple",
            headers=self.cols_mixes.headers_dict(),  # data is dict, headers too
        )
        self.p(tabulated, _log=None)

    def tab_mix_info_header(self, mix_info):
        self.p(
            tab([mix_info], tablefmt="plain", headers=self.cols_mixinfo.headers_list()),
            _log=None,
        )

    def really_add_track(self, track_to_add, release_name, mix_id, pos):
        _answ = self.ask(
            f'Add "{track_to_add.upper()}" on "{release_name}" to '
            f'mix #{mix_id}, at position {pos}? (Y/n) '
        )
        if _answ.lower() == "y" or _answ == "":
            return True
        return False

    def really_delete_track(self, track_pos, mix_name):
        really_del = self.ask(f'Delete Track {track_pos} '
                              f'from mix "{mix_name}"? (y/N) ')
        if really_del.lower() == "y":
            return True
        return False

    def really_delete_mix(self, mix_id, mix_name):
        really_delete = self.ask(
            f'Are you sure you want to delete mix "{mix_id} - {mix_name} "'
            'and all its containing tracks?'
        )
        if really_delete.lower() == "y":
            return True
        return False

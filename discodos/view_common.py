from discodos.utils import is_number, join_sep
import logging
#  import pprint
from datetime import datetime
from datetime import date
# from collections import OrderedDict

log = logging.getLogger('discodos')


class Headers_list():
    def __set_name__(self, owner, name) -> str:
        self.name = name
        self.dict_name = self.name.replace('_list_', '_dict_')

    def __get__(self, obj, type=None) -> object:
        return [val for val in obj.__dict__.get(self.dict_name).values()]

    # def __set__(self, obj, value) -> None:
    #     obj.__dict__[self.name] = value


class TableDefaults():
    '''Describes default and general settings for CLI and GUI tables.

    Generates headers dicts we use for CLI tables with tabulate.
    Generates headers lists we use for Qt Tree/TableViews and CLI tables.
    '''
    def __init__(self):
        # self.cols = OrderedDict()
        self.cols = {}

    def addcol(self, **kwargs):
        self.cols[kwargs.get('name')] = kwargs
        del(self.cols[kwargs.get('name')]['name'])

    def headers_list(self):
        return [col['caption'] for col in self.cols.values()]

    def headers_dict(self):
        return {
            name: settings['caption'] for (name, settings) in self.cols.items()
        }

    def get_locked_columns(self):
        """Retrieves a list of non-editable columns from self.cols dict.

        Returns:
            list: containing id's (int) of non-editable columns
        """
        cols_list = []
        for col_id, col_default in self.cols.items():
            edit = col_default.get("edit")
            if edit is False or edit is None:
                cols_list.append(col_id)
        return cols_list


class View_common():
    """ Common view utils, usable in CLI and GUI

    This class, Mix_view_common and Collection_view_common contain
    (default)settings and utilities for displaying data in GUI and CLI.

    Dictionaries containing SQL table fields translated to human readable
    column names.

        self.headers_dict_mixtracks_all:
            canvas for headers_list...
        self.headers_dict_mixtracks_all_short:
            same as headers_dict_mixtracks_all but some column's width is
            shortened by using abbreviations and linebreaks. Used in mix-tracks
            view (verbose mode: -v).

    Plain lists derived from headers dictionaries.

        self.headers_list_mixtracks_all:
            headers tracklist view in GUI
        self.headers_list_mixtracks_all_short:
            unused
    """
    # headers_list_mixtracks_all = Headers_list()
    # headers_list_mixtracks_all_short = Headers_list()

    def __init__(self):
        super().__init__()
        self.headers_dict_mixtracks_all = {
            'track_pos': '#', 'discogs_title': 'Release',
            'd_artist': 'Artist', 'd_track_name': 'Title',
            'd_track_no': 'Trk\nNo', 'key': 'Key', 'bpm': 'BPM',
            'key_notes': 'Key\nNotes', 'trans_rating': 'Transition\nRating',
            'trans_notes': 'Transition\nNotes', 'notes': 'Track\nNotes'
        }
        self.headers_dict_mixtracks_all_short = self.headers_dict_mixtracks_all.copy()
        self.headers_dict_mixtracks_all_short['d_artist'] = 'Track\nArtist'
        self.headers_dict_mixtracks_all_short['d_track_name'] = 'Track\nName'
        self.headers_dict_mixtracks_all_short['trans_rating'] = 'Trans.\nRating'
        self.headers_dict_mixtracks_all_short['trans_notes'] = 'Trans.\nNotes'

    def shorten_timestamp(self, sqlite_date, text=False):
        ''' remove time from timestamps we get out of the db, just leave date'''
        try:
            date_only = datetime.fromisoformat(self.none_replace(sqlite_date)).date()
            if text is True:
                return str(date_only)
            return date_only
        except ValueError as valerr:
            # log.debug(
            #  "VIEW: Can't convert date, returning dash {}".format(valerr))
            if text:
                return '-'
            raise valerr

    def format_date_month(self, sqlite_date, text=False):
        ''' format a date string to eg "May 2020" '''
        try:
            date_year_month = date.fromisoformat(
                self.none_replace(sqlite_date)).strftime("%b %Y")
        except ValueError:
            date_year_month = "-"

        if text is True:
            return str(date_year_month)
        return date_year_month

    def get_max_width(self, rows_list, keys_list, extra_space):
        '''gets max width of sqlite list of rows for given fields (keys_list)
           and add some space. FIXME: Only supports exactly 2 keys.'''
        max_width = 0
        for row in rows_list:
            row_mutable = dict(row)
            width = 0
            if row_mutable[keys_list[0]] is None:
                row_mutable[keys_list[0]] = "-"
            if row_mutable[keys_list[1]] is None:  # this is chosen_bpm field
                row_mutable[keys_list[1]] = "-"
            width = (len(row_mutable[keys_list[0]]) + len('/')
                     + len(str(row_mutable[keys_list[1]])))
            # log.debug("This rows width: {}.".format(width))
            if max_width < width:
                max_width = width
        log.debug("Found a max width of {}, adding extra_space of {}.".format(
                  max_width, extra_space))
        return max_width + extra_space

    def combine_fields_to_width(self, row, keys_list, set_width):
        '''takes sqlite row and keys_list, combines and fills with
           spaces up to set_width. FIXME: Only supports exactly 2 keys.'''
        row_mut = dict(row)  # make sqlite row tuple mutable
        # print(row_mut[keys_list[0]])
        # print(row_mut[keys_list[1]])
        if row_mut[keys_list[0]] is None:
            row_mut[keys_list[0]] = "-"
        if row_mut[keys_list[1]] is None:  # this is chosen_bpm field
            row_mut[keys_list[1]] = "-"
        combined_key_bpm = "{}/{}".format(
            row_mut[keys_list[0]],
            str(row_mut[keys_list[1]])
        )
        combined_with_space = combined_key_bpm.ljust(set_width)
        # log.warning("Combined string: {}".format(combined_with_space))
        return combined_with_space

    def none_replace(self, value_to_check):
        '''replaces string "None" by empty string
           (eg. we use this to pretty empty db-fields in tkinter gui)
           empty list will be replaced by zero, so tkinter can measure something
           spaces (" ") will be replaced by empty string as well
        '''

        if value_to_check == "None":
            value_to_check = ""

        elif value_to_check == " ":
            value_to_check = ""

        # elif value_to_check == []:
        #     value_to_check = [X]

        if value_to_check is None:
            value_to_check = ""

        return value_to_check

    def trim_table_fields(self, tuple_table, cut_pos=16, exclude=[]):
        """this method puts \n after a configured amount of characters
        into _all_ fields of a sqlite row objects tuple list"""
        log.info("VIEW: Trimming table field width "
                 "to max {} chars".format(cut_pos))
        # First convert list of tuples to list of dicts:
        table_nl = [dict(row) for row in tuple_table]
        # Now put newlines if longer than cut_pos chars
        for i, row in enumerate(table_nl):
            for key, field in row.items():
                if (
                    not is_number(field)
                    and field is not None
                    and key not in exclude
                ):
                    field_length = len(field)
                    if field_length < cut_pos:  # Exit early on short fields
                        continue
                    log.debug("String to be cut: {}".format(field))
                    possible_cuts = int(field_length / cut_pos)
                    log.debug("possible_cuts: {}".format(possible_cuts))
                    edited_field = ''
                    prev_cut_pos_space = 0
                    loops = range(1, possible_cuts + 1)
                    log.debug("We will loop {} time(s)".format(len(loops)))

                    # Run as often as cut possibilities exist
                    for cycle in loops:
                        log.debug("Cycle {}/{}".format(cycle, len(loops)))
                        # In each cycle we'll put \n _roughly_around_here_.
                        curr_cut_pos = cut_pos * cycle
                        log.debug("cur_cut_pos: %s", curr_cut_pos)
                        cut_pos_space = field.find(" ", curr_cut_pos)
                        log.debug("Next space after curr_cut_pos is at %s",
                                  cut_pos_space)
                        # If no is space following (almost at end),
                        # don't append newline, just append as-is!
                        if cut_pos_space == -1:
                            log.debug("No more space following. "
                                      "Add part and break loop!")
                            edited_field += field[prev_cut_pos_space:]
                            break
                        else:
                            log.debug("Add part and continue loop "
                                      "(if a cycle left)")
                            edited_field += field[prev_cut_pos_space:cut_pos_space] + "\n"
                        log.debug("From previous cut pos to current: {}".format(
                            field[prev_cut_pos_space:cut_pos_space])
                        )
                        log.debug("")
                        # Save pos for next cycle and skip the space itself,
                        # we don't want following lines to start with a space!
                        prev_cut_pos_space = cut_pos_space + 1

                    if field_length > cut_pos_space and cut_pos_space != -1:
                        log.debug(
                            "Loop done, appending remaining chars: "
                            "{} to {}".format(cut_pos_space, field_length)
                        )
                        # Add 1 to pos, we don't want a leading space.
                        edited_field += field[cut_pos_space + 1:]

                    log.debug("FINAL with newlines:")
                    log.debug("{}".format(edited_field))
                    log.debug("")
                    table_nl[i][key] = edited_field
        log.debug("table_nl has {} lines".format(len(table_nl)))
        return table_nl

    def replace_key_bpm(self, list_of_rows):
        '''show key,bpm from accousticbrainz but override with user-defined
           values if present'''
        log.info('VIEW: replace key, bpm data with AccousticBrainz data')
        # first convert list of rows to list of dicts:
        table = [dict(row) for row in list_of_rows]
        # now look for acousticbrainz values and replace if necessary
        for i, row in enumerate(table):
            if row['a_key'] and not row['key']:
                if row['a_chords_key'] != row['a_key']:
                    table[i]['key'] = '{}/{}*'.format(row['a_key'],
                                                      row['a_chords_key'])
                else:
                    table[i]['key'] = '{}*'.format((row['a_key']))
            if row['a_bpm'] and not row['bpm']:
                table[i]['bpm'] = '{}*'.format(round(float(row['a_bpm']), 1))
            # in any case remove acousticbrainz fields
            del(table[i]['a_key'])
            del(table[i]['a_chords_key'])
            del(table[i]['a_bpm'])
        return table

    def link_to(self, service, id):
        '''return link to either Discgos release, MusicBrainz Release/Recording
           or AcousticBrainz recording entries.
           Method currently does no sanity checking at all!
        '''
        if service == 'discogs release':
            return 'https://discogs.com/release/{}'.format(id)
        elif service == 'discogs master release':
            return 'https://discogs.com/master/{}'.format(id)
        elif service == 'musicbrainz release':
            return 'https://musicbrainz.org/release/{}'.format(id)
        elif service == 'musicbrainz recording':
            return 'https://musicbrainz.org/recording/{}'.format(id)
        elif service == 'acousticbrainz recording':
            return 'https://acousticbrainz.org/{}'.format(id)
        else:
            return 'Unknown online service'

    def replace_brainz(self, list_of_rows):
        '''compile a links field combining accousticbrainz, musicbrainz, discogs links
           into one field, then remove (mb)id fields'''
        log.info('VIEW: compile and put links field into mix_table.')
        # first convert list of rows to list of dicts - should be done already actually
        table = [dict(row) for row in list_of_rows]
        # now look for (mb)id values and put to list if necessary
        for i, row in enumerate(table):
            methods = []
            if row['release_match_method']:
                methods.append(row['release_match_method'])
            if row['track_match_method']:
                methods.append(row['track_match_method'])
            methods_str = join_sep(methods, '\n')
            table[i]['methods'] = methods_str

            times = []
            if row['release_match_time']:
                times.append(self.shorten_timestamp(row['release_match_time']))
            if row['track_match_time']:
                times.append(self.shorten_timestamp(row['track_match_time']))
            times_str = join_sep(times, '\n')
            table[i]['times'] = times_str

            links_str = self.join_links_to_str(row)
            table[i]['links'] = links_str

            # del from list what we don't need anymore
            del(table[i]['m_rel_id_override'])
            del(table[i]['m_rel_id'])
            del(table[i]['discogs_id'])
            del(table[i]['m_rec_id_override'])
            del(table[i]['m_rec_id'])
            del(table[i]['release_match_method'])
            del(table[i]['track_match_method'])
            del(table[i]['release_match_time'])
            del(table[i]['track_match_time'])
        return table

    def join_links_to_str(self, row):
        links = []
        # print(row.keys())
        if 'm_rel_id' in row.keys():
            if row['m_rel_id_override'] is not None:
                links.append(self.link_to('musicbrainz release',
                             row['m_rel_id_override']))
            elif row['m_rel_id'] is not None:
                links.append(self.link_to('musicbrainz release',
                             row['m_rel_id']))
        if 'm_rec_id' in row.keys():
            if row['m_rec_id_override'] is not None:
                links.append(self.link_to('musicbrainz recording',
                             row['m_rec_id_override']))
                links.append(self.link_to('acousticbrainz recording',
                             row['m_rec_id_override']))
            elif row['m_rec_id'] is not None:
                links.append(self.link_to('musicbrainz recording',
                             row['m_rec_id']))
                links.append(self.link_to('acousticbrainz recording',
                             row['m_rec_id']))
        if 'discogs_id' in row.keys() and row['discogs_id'] is not None:
            links.append(self.link_to('discogs release', row['discogs_id']))
        links_str = join_sep(links, '\n')
        return links_str

    def strfdelta(self, tdelta, fmt):
        d = {"days": tdelta.days}
        d["hours"], rem = divmod(tdelta.seconds, 3600)
        d["minutes"], d["seconds"] = divmod(rem, 60)
        return fmt.format(**d)


class Mix_view_common():
    ''' Constants and utils used for viewing Mixes. Usable in CLI and GUI.

    Lists of questions. Used in CLI:
        self._edit_track_questions: when editing a mix-track.
        self._edit_mix_questions: when editing a mixes info.

    Dictionaries containing SQL table fields translated to human readable
    column names. Mostly used for tabulate CLI tables:

        self.headers_dict_mixes:
            headers mixes overview.
        self.headers_dict_mixinfo:
            canvas for headers_list_mixinfo.
        self.headers_dict_mixtracks_brainz:
            headers mix-tracks view (*brainz mode -vv).
        self.headers_dict_mixtracks_basic:
            headers mix-tracks view (basic mode).

    Plain lists derived from headers dictionaries. Mostly used in GUI:

        self.headers_list_mixes:
            unused
        self.headers_list_mixinfo:
            header line of mix-tracks view on CLI (all modes).
        self.headers_list_mixtracks_brainz:
            unused
        self.headers_list_mixtracks_basic:
            unused

    Column defaults for visible-state and width. Used in GUI:

        self.cols_mixes
        self.cols_mixtracks
    '''
    headers_list_mixinfo = Headers_list()
    headers_list_mixtracks_brainz = Headers_list()
    headers_list_mixtracks_basic = Headers_list()

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
        # Tracklist mix info
        self.headers_dict_mixinfo = {
            'mix_id': 'Mix',
            'name': 'Name',
            'created': 'Created',
            'updated': 'Updated',
            'played': 'Played',
            'venue': 'Venue'
        }
        # Tracklist *brainz view header
        self.headers_dict_mixtracks_brainz = {
            'track_pos': '#',
            'discogs_title': 'Release',
            'd_artist': 'Track\nArtist',
            'd_track_name': 'Track\nName',
            'd_track_no': 'Trk\nNo',
            'key': 'Key',
            'bpm': 'BPM',
            'd_catno': 'Discogs\nCatNo',
            'methods': 'Rel match via\nRec match via',
            'times': 'Matched\non',
            'links': 'Links (MB Release, MB Recording, AB Recording, Discogs Release)'
        }
        # Tracklist basic view header
        self.headers_dict_mixtracks_basic = {
            'track_pos': '#',
            'd_catno': 'CatNo',
            'discogs_title': 'Release',
            'd_track_no': 'Trk\nNo',
            'trans_rating': 'Trans.\nRating',
            'key': 'Key',
            'bpm': 'BPM'
        }
        # Mixes column defaults
        self.cols_mixes = TableDefaults()
        self.cols_mixes.addcol(name='mix_id', order_id=0,
                               width=30, hidden=True, edit=False,
                               caption='#')
        self.cols_mixes.addcol(name='name', order_id=1,
                               width=None, hidden=False, edit=True,
                               caption='Name')
        self.cols_mixes.addcol(name='played', order_id=2,
                               width=90, hidden=False, edit=True,
                               caption='Played')
        self.cols_mixes.addcol(name='venue', order_id=3,
                               width=None, hidden=False, edit=True,
                               caption='Venue')
        self.cols_mixes.addcol(name='created', order_id=4,
                               width=None, hidden=True, edit=False,
                               caption='Created')
        self.cols_mixes.addcol(name='updated', order_id=5,
                               width=None, hidden=True, edit=False,
                               caption='Updated')
        # Tracklist column defaults
        self.cols_mixtracks = TableDefaults()
        self.cols_mixtracks.addcol(
            name='track_pos',
            order_id=0, width=30, hidden=False, edit=False,
            caption='#')
        self.cols_mixtracks.addcol(
            name='discogs_title',
            order_id=1, width=None, hidden=True, edit=False,
            caption='Release')
        self.cols_mixtracks.addcol(
            name='d_artist',
            order_id=2, width=120, hidden=False, edit=False,
            caption='Artist', short_cap='Artist\nName')
        self.cols_mixtracks.addcol(
            name='d_track_name',
            order_id=3, width=180, hidden=False, edit=False,
            caption='Title', short_cap='Track\nName')
        self.cols_mixtracks.addcol(
            name='track_no',
            order_id=4, width=30, hidden=False, edit=True,
            caption='Trk\nNo')
        self.cols_mixtracks.addcol(
            name='key',
            order_id=5, width=50, hidden=False, edit=True,
            caption='Key')
        self.cols_mixtracks.addcol(
            name='bpm',
            order_id=6, width=45, hidden=False, edit=True,
            caption='BPM')
        self.cols_mixtracks.addcol(
            name='key_notes',
            order_id=7, width=58, hidden=False, edit=True,
            caption='Key\nNotes')
        self.cols_mixtracks.addcol(
            name='trans_rating',
            order_id=8, width=58, hidden=False, edit=True,
            caption='Transition\nRating', short_cap='Trans.\nRating')
        self.cols_mixtracks.addcol(
            name='trans_notes',
            order_id=9, width=58, hidden=False, edit=True,
            caption='Transition\nNotes', short_cap='Trans.\nNotes')
        self.cols_mixtracks.addcol(
            name='notes',
            order_id=10, width=55, hidden=False, edit=True,
            caption='Track\nNotes')
        # print(self.cols_mixtracks.headers_list())

    def shorten_mixes_timestamps(self, mixes):
        ''' Reformats timestamps in a list of mixes.

        Argument mixes, usually an sqlite tuples list, will be translated into a
        list of mutable dicts. If it's one already, it's done anyway.
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


class Collection_view_common():
    """Collection view utils, usable in CLI and GUI, related to Collection only

    Lists of questions. Used in CLI:
        self._edit_track_questions: when editing a collection-track.

    Dictionaries/lists containing SQL table fields translated to human readable
    column names:
        self.headers_dict_search_results:
            canvas for headers_list_search_results
        self.headers_list_search_results:
            headers in GUI Search Results

    Column defaults for visible-state and width. Used in GUI:
        self.cols_search_results
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
        # Search Results column defaults
        self.cols_search_results = TableDefaults()
        self.cols_search_results.addcol(name='d_artist', order_id=0,
                                        width=120, hidden=False, edit=False,
                                        caption='Artist')
        self.cols_search_results.addcol(name='d_track_name', order_id=1,
                                        width=180, hidden=False, edit=False,
                                        caption='Title')
        self.cols_search_results.addcol(name='d_catno', order_id=2,
                                        width=90, hidden=False, edit=False,
                                        caption='Catalog')
        self.cols_search_results.addcol(name='d_track_no', order_id=3,
                                        width=30, hidden=False, edit=False,
                                        caption='Trk\nNo')
        self.cols_search_results.addcol(name='key', order_id=4,
                                        width=50, hidden=False, edit=False,
                                        caption='Key')
        self.cols_search_results.addcol(name='BPM', order_id=5,
                                        width=45, hidden=False, edit=False,
                                        caption='BPM')
        self.cols_search_results.addcol(name='key_notes', order_id=6,
                                        width=58, hidden=False, edit=False,
                                        caption='Key\nNotes')
        self.cols_search_results.addcol(name='', order_id=7,
                                        width=58, hidden=False, edit=False,
                                        caption='Track\nNotes')
        self.cols_search_results.addcol(name='discogs_id', order_id=8,
                                        width=70, hidden=False, edit=False,
                                        caption='Discogs\nRelease')
        self.cols_search_results.addcol(name='discogs_title', order_id=9,
                                        width=None, hidden=True, edit=False,
                                        caption='Release\nTitle')
        self.cols_search_results.addcol(name='import_timestamp', order_id=10,
                                        width=None, hidden=True, edit=False,
                                        caption='Imported')
        self.cols_search_results.addcol(name='in_d_coll', order_id=11,
                                        width=30, hidden=True, edit=False,
                                        caption='In D.\nColl.')
        self.cols_search_results.addcol(name='m_rec_id', order_id=12,
                                        width=80, hidden=True, edit=False,
                                        caption='MusicBrainz\nRecording')
        self.cols_search_results.addcol(name='m_rec_id_override', order_id=13,
                                        width=80, hidden=False, edit=True,
                                        caption='MusicBrainz\nRecording\nID-Override')
        self.cols_search_results.addcol(name='recording_match_method', order_id=14,
                                        width=100, hidden=True, edit=False,
                                        caption='MusicBrainz\nRecording\nMatch-Method')
        self.cols_search_results.addcol(name='recording_match_time', order_id=15,
                                        width=100, hidden=True, edit=False,
                                        caption='MusicBrainz\nRecording\nMatch-Time')
        self.cols_search_results.addcol(name='m_rel_id', order_id=16,
                                        width=80, hidden=True, edit=False,
                                        caption='MusicBrainz\nRelease')
        self.cols_search_results.addcol(name='release_match_method', order_id=17,
                                        width=100, hidden=True, edit=False,
                                        caption='MusicBrainz\nRelease\nMatch-Method')
        self.cols_search_results.addcol(name='release_match_time', order_id=18,
                                        width=100, hidden=True, edit=False,
                                        caption='MusicBrainz\nRelease\nMatch-Time')

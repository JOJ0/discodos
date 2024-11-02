import logging
from datetime import date, datetime, timedelta
from time import time
from tabulate import tabulate as tab

from discodos.utils import is_number, join_sep

log = logging.getLogger('discodos')


class HeadersList():
    """Currently unused"""
    # def __set__(self, obj, value) -> None:
    #     obj.__dict__[self.name] = value

    def __set_name__(self, owner, name) -> str:
        self.name = name
        self.dict_name = self.name.replace('_list_', '_dict_')

    def __get__(self, obj, type=None) -> object:
        return [val for val in obj.__dict__.get(self.dict_name).values()]


class ViewCommon():
    """ Common view utils, usable in CLI and GUI

    This class, MixViewCommon and CollectionViewCommon contain
    (default) settings and utilities for displaying data in GUI and CLI.

    Column defaults and headers. Used in GUI and CLI:
        self.cols_mixtracks (mix -v mixname, TableViewTracks)
        self.cols_search_results (TableViewResults)

    Column headers. Used in CLI:
        self.cols_mixes (mix)
        self.cols_mixinfo (mix mixname (header line showing mix info))
        self.cols_mixtracks_brainz (mix -vv mixname)
        self.cols.mixtracks_basic (mix mixname)
    """
    def __init__(self):
        super().__init__()
        # Mixes column defaults and headers for GUI and CLI
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
        # Tracklist mix info
        self.cols_mixinfo = TableDefaults()
        self.cols_mixinfo.addcol(name='mix_id', caption='Mix')
        self.cols_mixinfo.addcol(name='name', caption='Name')
        self.cols_mixinfo.addcol(name='created', caption='Created')
        self.cols_mixinfo.addcol(name='updated', caption='Updated')
        self.cols_mixinfo.addcol(name='played', caption='Played')
        self.cols_mixinfo.addcol(name='venue', caption='Venue')
        # Tracklist column defaults and headers for GUI and CLI
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
            name='d_track_no',
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
        # Tracklist *brainz view header
        self.cols_mixtracks_brainz = TableDefaults()
        self.cols_mixtracks_brainz.addcol(name='track_pos',
                                          caption='#')
        self.cols_mixtracks_brainz.addcol(name='discogs_title',
                                          caption='Release')
        self.cols_mixtracks_brainz.addcol(name='d_artist',
                                          caption='Track\nArtist')
        self.cols_mixtracks_brainz.addcol(name='d_track_name',
                                          caption='Track\nName')
        self.cols_mixtracks_brainz.addcol(name='d_track_no',
                                          caption='Trk\nNo')
        self.cols_mixtracks_brainz.addcol(name='key',
                                          caption='Key')
        self.cols_mixtracks_brainz.addcol(name='bpm',
                                          caption='BPM')
        self.cols_mixtracks_brainz.addcol(name='d_catno',
                                          caption='Discogs\nCatNo')
        self.cols_mixtracks_brainz.addcol(name='methods',
                                          caption='Rel match via\nRec match via')
        self.cols_mixtracks_brainz.addcol(name='times',
                                          caption='Matched\non')
        self.cols_mixtracks_brainz.addcol(name='links',
                                          caption='Links (MB Release, MB Recording, AB Recording, Discogs Release)')
        # Tracklist basic view header
        self.cols_mixtracks_basic = TableDefaults()
        self.cols_mixtracks_basic.addcol(name='track_pos',
                                         caption='#')
        self.cols_mixtracks_basic.addcol(name='d_catno',
                                         caption='CatNo')
        self.cols_mixtracks_basic.addcol(name='discogs_title',
                                         caption='Release')
        self.cols_mixtracks_basic.addcol(name='d_track_no',
                                         caption='Trk\nNo')
        self.cols_mixtracks_basic.addcol(name='trans_rating',
                                         caption='Trans.\nRating')
        self.cols_mixtracks_basic.addcol(name='key',
                                         caption='Key')
        self.cols_mixtracks_basic.addcol(name='bpm',
                                         caption='BPM')
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
                                        width=50, hidden=False, edit=True,
                                        caption='Key')
        self.cols_search_results.addcol(name='BPM', order_id=5,
                                        width=45, hidden=False, edit=True,
                                        caption='BPM')
        self.cols_search_results.addcol(name='key_notes', order_id=6,
                                        width=58, hidden=False, edit=True,
                                        caption='Key\nNotes')
        self.cols_search_results.addcol(name='notes', order_id=7,
                                        width=58, hidden=False, edit=True,
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
                                        width=30, hidden=True, edit=True,
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

    def html_link(self, url, caption=''):
        '''Wraps a url into html. Optionally a caption can be passed.'''
        caption = caption if caption else url
        return f"<a href={url}>{caption}</font></a>"

    def replace_linebreaks(self, text):
        '''Generally replaces all linebreaks with spaces but keeps

        the second found one (pidx < 3 --> part0 \n part2 \n).
        This is e.g used to shorten left column labels in info box in GUI.
        '''
        name_parts = re.findall(r'\S+|\s', text)
        new_text = ''
        for pidx, part in enumerate(name_parts):
            if pidx < 3:
                if part == '\n':
                    new_text += ' '
                else:
                    new_text += part
            else:
                if len(text) < 20 and part == '\n':
                    new_text += ' '
                else:
                    new_text += part
        return new_text


class ViewCommonCommandline(ViewCommon):
    """ Common view utils, usable in CLI only.
    """

    def p(self, message, logging="", lead_nl=False, trail_nl=True):
        if logging == "debug":
            log.debug(message)
        if logging == "info":
            log.info(message)
        if lead_nl is True and trail_nl is True:
            print('\n' + str(message) + '\n')
        elif lead_nl is True:
            print('\n' + str(message))
        elif trail_nl is True:
            print('' + str(message) + '\n')

    def ask(self, text=""):
        ''' ask user for something and return answer '''
        return input(text)

    def ask_for_track(self, suggest='A1'):
        track_no = self.ask("Which track? ({}) ".format(suggest))
        if track_no == '':
            return suggest
        return track_no

    def tab_mix_table(self, mix_data, _verbose=False, brainz=False, format=""):
        mix_data_key_bpm = self.replace_key_bpm(mix_data)
        mix_data_nl = self.trim_table_fields(mix_data_key_bpm)

        # for row in mix_data_nl:  # DEBUG
        #    log.debug(str(row))
        # log.debug("")

        if _verbose:
            self.p(tab(
                mix_data_nl,
                tablefmt='pipe' if not format else format,
                headers=self.cols_mixtracks.headers_dict(short=True)
            ))
        elif brainz:
            mix_data_brainz = self.replace_brainz(mix_data_key_bpm)
            mix_data_brainz_nl = self.trim_table_fields(
                mix_data_brainz,
                exclude=['methods']
            )
            self.p(tab(
                mix_data_brainz_nl,
                tablefmt='grid' if not format else format,
                headers=self.cols_mixtracks_brainz.headers_dict()
            ))
        else:
            self.p(tab(
                mix_data_nl,
                tablefmt='pipe' if not format else format,
                headers=self.cols_mixtracks_basic.headers_dict()
            ))

    def duration_stats(self, start_time, msg):
        took_seconds = time() - start_time
        if took_seconds >= 86400:
            days_part = "{days} days "
        else:
            days_part = ""
        took_str = self.strfdelta(
            timedelta(seconds=took_seconds),
            days_part + "{hours} hours {minutes} minutes {seconds} seconds"
        )
        msg_took = "{} took {}".format(msg, took_str)
        log.info('CTRLS: {} took {} seconds'.format(msg, took_seconds))
        log.info('CTRLS: {}'.format(msg_took))
        print(msg_took)

    def edit_ask_details(self, orig_data, edit_questions):
        # collect answers from user input
        answers = {}
        for db_field, question in edit_questions:
            # some special treatments for track_pos handling...
            if db_field == 'track_pos':
                answers['track_pos'] = self.ask(question.format(orig_data['track_pos']))
                if answers['track_pos'] == '':
                    log.info("Answer was empty, dropping item from update.")
                    del(answers['track_pos'])
                elif not is_number(answers['track_pos']):
                    while not is_number(answers['track_pos']):
                        log.warning("Answer was not a number, asking again.")
                        if answers['track_pos'] == '':
                            del(answers['track_pos'])
                            break
                        else:
                            answers['track_pos'] = self.ask(question.format(orig_data['track_pos']))
                else:
                    move_to = int(answers['track_pos'])
                    if move_to < orig_data['track_pos']:
                        mvmsg = 'Note: Tracks new position will be right _before_ '
                        mvmsg+= 'current track {}'.format(move_to)
                        log.debug(mvmsg)
                        print(mvmsg)
                    elif move_to > orig_data['track_pos']:
                        mvmsg = 'Note: Tracks new position will be right _after_ '
                        mvmsg+= 'current track {}'.format(move_to)
                        log.debug(mvmsg)
                        print(mvmsg)
            elif db_field == 'trans_rating':
                allowed = ['++', '+', '~', '-', '--']
                answers['trans_rating'] = self.ask(question.format(
                    orig_data['trans_rating']
                ))
                if answers['trans_rating'] == '':
                    log.info("Answer was empty, dropping item from update.")
                    del(answers['trans_rating'])
                else:
                    while not answers['trans_rating'] in allowed:
                        log.warning("Please use one of the following: "
                                    "++, +, ~, -, --")
                        if answers['trans_rating'] == '':
                            del(answers['trans_rating'])
                            break
                        else:
                            answers['trans_rating'] = self.ask(question.format(orig_data['trans_rating']))
            elif db_field == 'name':
                # initial user question
                answers['name'] = self.ask(question.format(orig_data['name']))
                # sanity checking loop
                while answers['name'] == orig_data['name']:
                    log.warning("Just press enter if you want to leave as-is.")
                    answers['name'] = self.ask(question.format(orig_data['name']))
                # after loop we know that existing and new are different
                # if answer is empty, leave as-is (no empty mixname allowed)
                if answers['name'] == '':
                    log.info("Answer was empty, dropping item from update.")
                    del(answers['name'])
            else:
                answers[db_field] = self.ask(question.format(
                    orig_data[db_field]
                ))
                if answers[db_field] == "":
                    log.info("Answer was empty, dropping item from update.")
                    del(answers[db_field])

        log.debug("CTRL: _edit_ask_details: answers dict: {}".format(answers))
        return answers

    def view_tutorial(self):
        tutorial_items = [
            '\n\nFirst things first: Whenever DiscoDOS asks you a question, '
            'you will be shown a default value in (brackets). If you '
            'are fine with the default, just press enter.'
            '\nWhen it\'s a yes/no question, the default will be presented as a '
            'capital letter. Let\'s try this right now:',

            '\n\nI will show a couple of basic commands now. Best you open a '
            'second terminal window (macOS/Linux) or command prompt window (Windows), '
            'so you can try out the commands over there, while watching this tutorial.',

            '\n\nImport your collection (1000 releases take about a minute or two '
            'to import):'
            '\ndisco import',

            '\n\nCreate a mix:'
            '\ndisco mix my_mix -c',

            '\n\nSearch in your collection and add tracks to the mix:\n'
            'disco mix my_mix -a "search terms"',

            '\n\nView your mix. Leave out mix-name '
            'to view a list of all your mixes:'
            '\ndisco mix my_mix',

            '\n\nDiscoDOS by default is minimalistic. The initial import only '
            'gave us release-titles/artists and CatNos. Now fetch track-names '
            'and track-artists:'
            '\ndisco mix my_mix -u',

            '\n\nNow let\'s have a look into the tracklist again. '
            '(-v enables a more detailed view, it includes eg '
            'track-names, artists, transition rating, notes, etc.)'
            '\ndisco mix my_mix -v',

            '\n\nMatch the tracks with MusicBrainz/AcousticBrainz and get '
            'BPM and musical key information (-z is quicker but not as accurate):'
            '\ndisco mix my_mix -zz',

            '\n\nIf we were lucky, some tracks will show BPM and key information. '
            'Hint if you\'re new to CLI tools: We typed this command already, you '
            'don\'t have to type or copy/paste it again, just use '
            'your terminals command history, usually by hitting the "cursor up" key '
            'until you see this command and just pressing enter:'
            '\ndisco mix my_mix -v',

            '\n\nView weblinks pointing directly to your Discogs & MusicBrainz releases, '
            'find out interesting details about your music via AcousticBrainz, '
            'and see how the actual matching went:'
            '\ndisco mix my_mix -vv',

            "\n\nIf a track couldn't be matched automatically, you could head over "
            'to the MusicBrainz website yourself, find a Recording MBID and put it '
            'into DiscoBASE by using the "edit track command" below. '
            'If you\'re done with editing, re-run the match-command from above '
            '(the one with -zz in the end ;-). Again: use the command history! '
            '\ndisco mix my_mix -e 1',

            '\n\nIf you\'re just interested in a tracks details and don\'t want to '
            'add it to a mix, use the search command. You can also combine it with '
            'the Discogs update or MusicBrainz update options.'
            '\ndisco search "search terms"'
            '\ndisco search "search terms" -u'
            '\ndisco search "search terms" -zz',

            "\n\nThere's a lot more you can do. Each subcommand has it's own help command:"
            '\ndisco mix -h'
            '\ndisco search -h'
            '\ndisco suggest -h',

            "\nStill questions? Check out the README or open an issue on Github: "
            'https://github.com/JOJ0/discodos'
        ]

        view_tut = self.ask('Do you want to see a tutorial on how DiscoDOS '
                            'basically works? (Y/n): ')
        if view_tut.lower() == 'y' or view_tut == '':
            # print(tutorial_items[0])
            i = 0
            while i < len(tutorial_items):
                print(tutorial_items[i])
                if i == len(tutorial_items) - 1:
                    break
                continue_tut = self.ask('\nContinue tutorial? (Y/n) ')
                if continue_tut.lower() == 'n':
                    break
                i += 1

    def welcome_to_discodos(self):
        print(r'''
                            _______  _______ ________
                           /       \        /       /
                          /  ___   /  ___  /  _____/
                         /  /  /  /  /  /  \____  \
                        /  /__/  /  /__/  _____/  /
Welcome to  D i s c o  /                /        /
                      /_______/\_______/________/
              ''')


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

    def headers_dict(self, short=False):
        if short:
            headers = {}
            for (name, settings) in self.cols.items():
                if settings.get('short_cap'):
                    headers[name] = settings['short_cap']
                else:
                    headers[name] = settings['caption']
            return headers
        return {
            name: settings['caption'] for (name, settings) in self.cols.items()
        }

    def get_locked_columns(self):
        """Retrieves a list of non-editable columns from self.cols dict.

        Returns:
            list: containing id's (int) of non-editable columns
        """
        cols_list = []
        for col_default in self.cols.values():
            edit = col_default.get('edit')
            if edit is False or edit is None:
                cols_list.append(col_default.get('order_id'))
        return cols_list

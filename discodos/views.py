from discodos.utils import is_number, join_sep
from abc import ABC, abstractmethod
import logging
from tabulate import tabulate as tab # should be only in views.py
import pprint
from datetime import datetime
from datetime import date
from time import time
from datetime import timedelta

log = logging.getLogger('discodos')


# common view utils, usable in CLI and GUI
class View_common(ABC):
    def shorten_timestamp(self, sqlite_date, text = False):
        ''' remove time from timestamps we get out of the db, just leave date'''
        try:
            date_only = datetime.fromisoformat(self.none_replace(sqlite_date)).date()
            if text == True:
                return str(date_only)
            return date_only
        except ValueError as valerr:
            #log.debug(
            #  "VIEW: Can't convert date, returning dash {}".format(valerr))
            if text:
                return '-'
            raise valerr

    def format_date_month(self, sqlite_date, text = False):
        ''' format a date string to eg "May 2020" '''
        try:
            date_year_month = date.fromisoformat(
                self.none_replace(sqlite_date)).strftime("%b %Y")
        except ValueError:
            date_year_month = "-"

        if text == True:
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
            if row_mutable[keys_list[1]] is None: # this is chosen_bpm field
                row_mutable[keys_list[1]] = "-"
            width = (len(row_mutable[keys_list[0]]) + len('/')
                + len(str(row_mutable[keys_list[1]])))
            #log.debug("This rows width: {}.".format(width))
            if max_width < width:
                max_width = width
        log.debug("Found a max width of {}, adding extra_space of {}.".format(
              max_width, extra_space))
        return max_width + extra_space

    def combine_fields_to_width(self, row, keys_list, set_width):
        '''takes sqlite row and keys_list, combines and fills with
           spaces up to set_width. FIXME: Only supports exactly 2 keys.'''
        row_mut = dict(row) # make sqlite row tuple mutable
        #print(row_mut[keys_list[0]])
        #print(row_mut[keys_list[1]])
        if row_mut[keys_list[0]] is None:
            row_mut[keys_list[0]] = "-"
        if row_mut[keys_list[1]] is None: # this is chosen_bpm field
            row_mut[keys_list[1]] = "-"
        combined_key_bpm = "{}/{}".format(row_mut[keys_list[0]],
              str(row_mut[keys_list[1]]))
        combined_with_space = combined_key_bpm.ljust(set_width)
        #log.warning("Combined string: {}".format(combined_with_space))
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

        #elif value_to_check == []:
        #    value_to_check = [X]

        if value_to_check == None:
            value_to_check = ""

        return value_to_check

    def trim_table_fields(self, tuple_table, cut_pos = 16, exclude = []):
        """this method puts \n after a configured amount of characters
        into _all_ fields of a sqlite row objects tuple list"""
        log.info('VIEW: Trimming table field width to max {} chars'.format(cut_pos))
        # first convert list of tuples to list of lists:
        table_nl = [dict(row) for row in tuple_table]
        # now put newlines if longer than cut_pos chars
        for i, row in enumerate(table_nl):
            for key, field in row.items():
                if (not is_number(field) and field is not None
                    and not key in exclude):
                    len_field = len(field)
                    if len_field > cut_pos:
                        possible_cuts = int(len_field / cut_pos)
                        log.info("possible_cuts: {}".format(possible_cuts))
                        edited_field = ''
                        prev_cut_pos_space = 0
                        log.debug("this is our range: {}".format(range(1, possible_cuts+1)))
                        for cycle in range(1, possible_cuts+1): # run as often as cut possibilities exist
                            log.debug("cycle {}".format(cycle))
                            curr_cut_pos = cut_pos * cycle # in each cycle we'd like to put \n _around_ here
                            log.debug("curr_cut_pos index: %s", curr_cut_pos)
                            cut_pos_space = field.find(' ', curr_cut_pos)
                            log.debug("cut_pos_space index (next space after curr_cut_pos): %s", cut_pos_space)
                            # if no space following (almost at end) don't add newline, just add as-is
                            if cut_pos_space == -1:
                                log.debug("No more space following. Add part and break loop!")
                                log.debug("")
                                edited_field += field[prev_cut_pos_space:]
                                break
                            else:
                                edited_field += field[prev_cut_pos_space:cut_pos_space] + "\n"
                            log.debug("from prev_cut_pos_space to cut_pos_space: {}".format(field[prev_cut_pos_space:cut_pos_space]))
                            log.debug("")
                            # save pos for next cycle and skip the space itself,
                            # we don't want following lines to start with a space!
                            prev_cut_pos_space = cut_pos_space + 1
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
        #print(row.keys())
        if 'm_rel_id' in row.keys():
            if row['m_rel_id_override']:
                links.append(self.link_to('musicbrainz release', row['m_rel_id_override']))
            elif row['m_rel_id']:
                links.append(self.link_to('musicbrainz release', row['m_rel_id']))
        if 'm_rec_id' in row.keys():
            if row['m_rec_id_override']:
                links.append(self.link_to('musicbrainz recording', row['m_rec_id_override']))
                links.append(self.link_to('acousticbrainz recording', row['m_rec_id_override']))
            elif row['m_rec_id']:
                links.append(self.link_to('musicbrainz recording', row['m_rec_id']))
                links.append(self.link_to('acousticbrainz recording', row['m_rec_id']))
        if 'discogs_id' in row.keys():
            if row['discogs_id']:
                links.append(self.link_to('discogs release', row['discogs_id']))
        links_str = join_sep(links, '\n')
        return links_str

    def strfdelta(self, tdelta, fmt):
        d = {"days": tdelta.days}
        d["hours"], rem = divmod(tdelta.seconds, 3600)
        d["minutes"], d["seconds"] = divmod(rem, 60)
        return fmt.format(**d)


# Mix view utils and data, usable in CLI and GUI, related to mixes only
class Mix_view_common(ABC):
    def __init__(self):
        # list of questions a user is asked when editing a mix-track
        # first list item is the related db-field, second is the question
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

        # list of questions a user is asked when editing a mixes info
        self._edit_mix_questions = [
            ["name", "Name ({}): "],
            ["played", "Played ({}): "],
            ["venue", "Venue ({}): "]
        ]

# Collection view utils, usable in CLI and GUI, related to Collection only
class Collection_view_common(ABC):
    def __init__(self):
        #super(Collection_view_cli, self).__init__()
        # list of questions a user is asked when searching and editing track
        # first list item is the related db-field, second is the question
        self._edit_track_questions = [
            ["key", "Key ({}): "],
            ["bpm", "BPM ({}): "],
            ["key_notes", "Key notes/bassline/etc. ({}): "],
            ["notes", "Other track notes: ({}): "],
            ["m_rec_id_override", "Override MusicBrainz Recording ID: ({}): "]
        ]

# common view utils, usable in CLI only
class View_common_cli(View_common):
    def p(self, message):
        print(''+str(message)+'\n')

    def ask(self, text=""):
        ''' ask user for something and return answer '''
        return input(text)

    def ask_for_track(self, suggest = 'A1'):
        track_no = self.ask("Which track? ({}) ".format(suggest))
        if track_no == '':
            return suggest
        return track_no

    def tab_mix_table(self, _mix_data, _verbose = False, brainz = False):
        _mix_data_key_bpm = self.replace_key_bpm(_mix_data)
        _mix_data_nl = self.trim_table_fields(_mix_data_key_bpm)
        #for row in _mix_data_nl: # debug only
        #   log.debug(str(row))
        #log.debug("")
        if _verbose:
            self.p(tab(_mix_data_nl, tablefmt='pipe',
              headers={'track_pos': '#', 'discogs_title': 'Release',
                       'd_artist': 'Track\nArtist', 'd_track_name': 'Track\nName',
                       'd_track_no': 'Trk\nNo', 'key': 'Key', 'bpm': 'BPM',
                       'key_notes': 'Key\nNotes', 'trans_rating': 'Trans.\nRating',
                       'trans_notes': 'Trans.\nNotes', 'notes': 'Track\nNotes'}))
        elif brainz:
            _mix_data_brainz = self.replace_brainz(_mix_data_key_bpm)
            _mix_data_brainz_nl = self.trim_table_fields(_mix_data_brainz,
                exclude = ['methods'])
            self.p(tab(_mix_data_brainz_nl, tablefmt='grid',
              headers={'track_pos': '#', 'discogs_title': 'Release',
                       'd_artist': 'Track\nArtist', 'd_track_name': 'Track\nName',
                       'd_track_no': 'Trk\nNo', 'key': 'Key', 'bpm': 'BPM',
                       'd_catno': 'Discogs\nCatNo',
                       'methods': 'Rel match via\nRec match via',
                       'times': 'Matched\non',
                       'links': 'Links (MB Release, MB Recording, AB Recording, Discogs Release)'
                       }))
        else:
            self.p(tab(_mix_data_nl, tablefmt='pipe',
              headers={'track_pos': '#', 'd_catno': 'CatNo', 'discogs_title': 'Release',
                       'd_track_no': 'Trk\nNo', 'trans_rating': 'Trns\nRat',
                       'key': 'Key', 'bpm': 'BPM'}))

    def duration_stats(self, start_time, msg):
        took_seconds = time() - start_time
        if took_seconds >= 86400:
            days_part = "{days} days "
        else:
            days_part = ""
        took_str = self.strfdelta(timedelta(seconds=took_seconds),
          days_part+"{hours} hours {minutes} minutes {seconds} seconds")
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
                answers['trans_rating'] = self.ask(
                      question.format(orig_data['trans_rating']))
                if answers['trans_rating'] == '':
                    log.info("Answer was empty, dropping item from update.")
                    del(answers['trans_rating'])
                else:
                    while not answers['trans_rating'] in allowed:
                        log.warning(
                          "Please use one of the following: ++, +, ~, -, --")
                        if answers['trans_rating'] == '':
                            del(answers['trans_rating'])
                            break
                        else:
                            answers['trans_rating'] = self.ask(question.format(orig_data['trans_rating']))
            elif db_field == 'name':
                # initial user question
                answers['name'] = self.ask(
                      question.format(orig_data['name']))
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
                answers[db_field] = self.ask(
                                         question.format(orig_data[db_field]))
                if answers[db_field] == "":
                    log.info("Answer was empty, dropping item from update.")
                    del(answers[db_field])

        log.debug("CTRL: _edit_ask_details: answers dict: {}".format(answers))
        return answers

    def view_tutorial(self):
        m ='Connection to your Discogs collection is working, '
        m+="but you didn't provide a command."
        print(m)
        tutorial_items = [
        '\n\nFirst things first: Whenever DiscoDOS asks you a question, you '
        'will be shown a default value in (brackets). If you '
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

        view_tut = self.ask(
        '\nDo you want to see a tutorial on how DiscoDOS basically works? (Y/n): ')
        if view_tut.lower() == 'y' or view_tut == '':
            #print(tutorial_items[0])
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


# viewing mixes in CLI mode:
class Mix_view_cli(Mix_view_common, View_common_cli, View_common):
    def __init__(self):
        super(Mix_view_cli, self).__init__()

    def tab_mixes_list(self, mixes_data):
        # make list of dicts out of the sqlite tuples list
        mixes = [dict(row) for row in mixes_data]
        for i, mix in enumerate(mixes): # shorten/format timestamps in this view
            mixes[i]['created'] = self.shorten_timestamp(mix['created'],
                  text = True)
            mixes[i]['played'] = self.format_date_month(mix['played'],
                  text = True)
            mixes[i]['updated'] = self.shorten_timestamp(mix['updated'],
                  text = True)
        tabulated = tab(self.trim_table_fields(mixes),
          tablefmt="simple", # headers has to be dict too!
          headers={'mix_id': '#', 'name': 'Name', 'played':'Played',
                   'venue': 'Venue', 'created': 'Created', 'updated': 'Updated'})
        self.p(tabulated)

    def tab_mix_info_header(self, mix_info):
        self.p(tab([mix_info], tablefmt="plain",
                headers=["Mix", "Name", "Created", "Updated", "Played", "Venue"]))

    def really_add_track(self, track_to_add, release_name, mix_id, pos):
        quest=(
        'Add "{}" on "{}" to mix #{}, at position {}? (Y/n) '
            .format(track_to_add.upper(), release_name, int(mix_id), pos))
        _answ = self.ask(quest)
        if _answ.lower() == "y" or _answ == "":
            return True

    def really_delete_track(self, track_pos, mix_name):
        really_del = self.ask('Delete Track {} from mix "{}"? (y/N) '.format(
              track_pos, mix_name))
        if really_del.lower() == "y":
             return True
        return False

    def really_delete_mix(self, mix_id, mix_name):
        really_delete = self.ask(
            'Are you sure you want to delete mix "{} - {}" and all its containing tracks? '.format(
                mix_id, mix_name))
        if really_delete.lower() == "y":
            return True
        return False



# viewing collection (search) outputs in CLI mode:
class Collection_view_cli(Collection_view_common, View_common_cli, View_common):
    def __init__(self):
        super(Collection_view_cli, self).__init__()

    def tab_online_search_results(self, _result_list):
        self.p(tab(_result_list, tablefmt="simple", headers={
          'id': 'ID', 'artist': 'Artist', 'title':'Release',
          'label': 'Label', 'country': 'C', 'year': 'Year', 'format': 'Format'}))

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
                if key_bpm_user == "()": # if empty, remove it completely
                    key_bpm_user = ""

                # do the same for brainz values:
                key_bpm_brainz = "("
                if tr['a_key']:
                    key_bpm_brainz+= tr['a_key'] + '*'

                if tr['a_key'] and tr['a_bpm']:
                    bpm_rnd = str(round(float(tr['a_bpm']),1))
                    key_bpm_brainz+= '/{}*'.format(bpm_rnd)
                elif tr['a_bpm']:
                    bpm_rnd = str(round(float(tr['a_bpm']),1))
                    key_bpm_brainz+= '{}*'.format(bpm_rnd)
                key_bpm_brainz += ')'
                if key_bpm_brainz == '()': # if empty, remove it completely
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
            row['artist_title_links'] = '{} - {}\n{}\n '.format(row['d_artist'],
                  row['discogs_title'], links_str)
            del(table[i]['m_rel_id_override'])
            del(table[i]['m_rel_id'])
            del(table[i]['discogs_id'])
            del(table[i]['d_artist'])
            del(table[i]['discogs_title'])
        table = self.trim_table_fields(table, 40)
        print(tab(table, tablefmt="grid",
            headers={'d_catno': 'CatNo',
              'artist_title_links': 'Release: Artist - Title - Links'}))

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

    def brainz_processed_report(self, processed, added_release, added_rec, added_key,
      added_chords_key, added_bpm, errors_db, errors_not_found, errors_no_rec_AB):
        msg_mb = 'Processed: {}.\nAdded MusicBrainz info to DiscoBASE: '.format(processed)
        msg_mb+= 'Release MBIDs: {}, Recording MBIDs: {}\n'.format(
            added_release, added_rec)
        msg_mb+= 'Added AccousticBrainz info: Key: {}, Chords Key: {}, BPM: {}\n'.format(
            added_key, added_chords_key, added_bpm)
        msg_mb+= 'No AcousticBrainz entries available yet: {} (consider submitting!)'.format(errors_no_rec_AB)

        msg_err = 'Database errors: {}. Not found on Discogs errors: {}.'.format(
            errors_db, errors_not_found)

        msg_note = 'Note in case you did an all-mix-tracks-match (disco mix -z): '
        msg_note+= 'Some of the processed tracks might be on the same release. '
        msg_note+= 'Thus, the total release count added in reality might be less.'
        print(msg_mb+'\n'+msg_err+'\n\n'+msg_note)
        log.info(msg_mb+'\n'+msg_err+'\n\n'+msg_note)
        print("") # space for readability

        msg1 = "If DiscoDOS didn't find many Release MBIDs or Recording MBIDs "
        msg1+= "please help improving the matching algorithm and either: "
        print(msg1)

        msg2 = "* Investigate yourself: Execute match command again with increased log-level: disco -v ...\n"
        msg2+= "* or just send the debug.log file (it's in your discodos folder)\n"
        msg2+= "In any case, please report by opening an issue on github.com/JOJ0/discodos"
        print(msg2+'\n')

    def brainz_processed_so_far(self, processed, processed_total):
        msg_proc='{}/{}'.format(processed, processed_total)
        log.info(msg_proc)
        print(msg_proc)

# CLI user interaction class - holds info about what user wants to do
# analyzes argparser args and puts it to nicely human readable properties
class User_int(object):
    def __init__(self, _args):
        self.args = _args
        self.WANTS_ONLINE = True
        self.WANTS_TO_LIST_ALL_RELEASES = False
        self.WANTS_TO_SEARCH_FOR_RELEASE = False
        self.WANTS_TO_ADD_TO_MIX = False
        self.WANTS_TO_SHOW_MIX_OVERVIEW = False
        self.WANTS_TO_SHOW_MIX_TRACKLIST = False
        self.WANTS_TO_CREATE_MIX = False
        self.WANTS_TO_EDIT_MIX_TRACK = False
        self.WANTS_TO_PULL_TRACK_INFO = False
        self.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE = False
        self.WANTS_VERBOSE_MIX_TRACKLIST = False
        self.WANTS_TO_REORDER_MIX_TRACKLIST = False
        self.WANTS_TO_ADD_AT_POSITION = False
        self.WANTS_TO_DELETE_MIX_TRACK = False
        self.WANTS_TO_ADD_RELEASE_IN_MIX_MODE = False
        self.WANTS_TO_ADD_AT_POS_IN_MIX_MODE = False
        self.WANTS_TO_COPY_MIX = False
        self.WANTS_TO_DELETE_MIX = False
        self.WANTS_SUGGEST_TRACK_REPORT = False
        self.WANTS_TO_BULK_EDIT = False
        self.WANTS_SUGGEST_BPM_REPORT = False
        self.WANTS_SUGGEST_KEY_REPORT = False
        self.WANTS_SUGGEST_KEY_AND_BPM_REPORT = False
        self.WANTS_TO_PULL_BRAINZ_INFO = False
        self.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = False
        self.BRAINZ_SEARCH_DETAIL = 1
        self.WANTS_MUSICBRAINZ_MIX_TRACKLIST = False
        self.WANTS_TO_EDIT_MIX = False
        self.DID_NOT_PROVIDE_COMMAND = False
        self.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS = False
        self.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ = False
        self.WANTS_TO_IMPORT_COLLECTION = False
        self.WANTS_TO_IMPORT_RELEASE = False
        self.WANTS_TO_ADD_AND_IMPORT_RELEASE = False
        self.WANTS_TO_IMPORT_COLLECTION_WITH_TRACKS = False
        self.WANTS_TO_IMPORT_COLLECTION_WITH_BRAINZ = False
        self.WANTS_TO_SEARCH_AND_EDIT_TRACK = False
        self.RESUME_OFFSET = 0
        self.WANTS_TO_LAUNCH_SETUP = False
        self.WANTS_TO_FORCE_UPGRADE_SCHEMA = False
        self.MIX_SORT = False


        # RELEASE MODE:
        if hasattr(self.args, 'release_search'):
            if self.args.release_search == "all":
                if self.args.search_discogs_update == True:
                    # discogs update all
                    self.WANTS_ONLINE = True
                    self.WANTS_TO_LIST_ALL_RELEASES = True
                    self.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS = True
                    if self.args.search_offset > 0:
                        self.RESUME_OFFSET = self.args.search_offset
                elif self.args.search_brainz_update != 0:
                    # brainz update all
                    self.WANTS_ONLINE = True
                    self.WANTS_TO_LIST_ALL_RELEASES = True
                    self.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ = True
                    if self.args.search_brainz_update > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2
                    if self.args.search_offset > 0:
                        self.RESUME_OFFSET = self.args.search_offset
                else:
                    # just list all
                    self.WANTS_ONLINE = False
                    self.WANTS_TO_LIST_ALL_RELEASES = True
            else:
                self.WANTS_TO_SEARCH_FOR_RELEASE = True
                if (self.args.add_to_mix != 0 and self.args.track_to_add != 0
                  and self.args.add_at_pos):
                    self.WANTS_TO_ADD_AT_POSITION = True
                if self.args.add_to_mix !=0 and self.args.track_to_add !=0:
                    self.WANTS_TO_ADD_TO_MIX = True
                if self.args.add_to_mix !=0:
                    self.WANTS_TO_ADD_TO_MIX = True

                if self.args.search_discogs_update !=0:
                    if self.args.offline_mode == True:
                        log.error("You can't do that in offline mode!")
                        raise SystemExit(1)
                    self.WANTS_TO_SEARCH_AND_UPDATE_DISCOGS = True
                elif self.args.search_brainz_update !=0:
                    if self.args.offline_mode == True:
                        log.error("You can't do that in offline mode!")
                        raise SystemExit(1)
                    self.WANTS_TO_SEARCH_AND_UPDATE_BRAINZ = True
                    self.BRAINZ_SEARCH_DETAIL = self.args.search_brainz_update
                    if self.args.search_brainz_update > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2
                elif self.args.search_edit_track == True:
                    self.WANTS_TO_SEARCH_AND_EDIT_TRACK = True


        # MIX MODE
        if hasattr(self.args, 'mix_name'):
            if self.args.mix_name == "all":
                self.WANTS_TO_SHOW_MIX_OVERVIEW = True
                self.WANTS_ONLINE = False
                if self.args.create_mix == True:
                    log.error("Please provide a mix name to be created!")
                    log.error("(Mix name \"all\" is not valid.)")
                    raise SystemExit(1)
                elif self.args.delete_mix == True:
                    log.error("Please provide a mix name or ID to be deleted!")
                    raise SystemExit(1)
                if self.args.discogs_update:
                    self.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    if self.args.mix_offset > 0:
                        self.RESUME_OFFSET = self.args.mix_offset
                if self.args.brainz_update:
                    self.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    self.BRAINZ_SEARCH_DETAIL = self.args.brainz_update
                    if self.args.brainz_update > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2
                    if self.args.mix_offset > 0:
                        self.RESUME_OFFSET = self.args.mix_offset
            else:
                self.WANTS_TO_SHOW_MIX_TRACKLIST = True
                self.WANTS_ONLINE = False
                if self.args.mix_sort:
                    self.MIX_SORT = self.args.mix_sort
                if self.args.create_mix:
                    self.WANTS_TO_CREATE_MIX = True
                    self.WANTS_ONLINE = False
                if self.args.edit_mix_track:
                    self.WANTS_TO_EDIT_MIX_TRACK = True
                    self.WANTS_ONLINE = False
                if self.args.verbose_tracklist == 1:
                    self.WANTS_VERBOSE_MIX_TRACKLIST = True
                    self.WANTS_ONLINE = False
                if self.args.verbose_tracklist == 2:
                    self.WANTS_MUSICBRAINZ_MIX_TRACKLIST = True
                    self.WANTS_ONLINE = False
                if self.args.reorder_from_pos:
                    self.WANTS_TO_REORDER_MIX_TRACKLIST = True
                    self.WANTS_ONLINE = False
                if self.args.delete_track_pos:
                    self.WANTS_TO_DELETE_MIX_TRACK = True
                    self.WANTS_ONLINE = False
                if self.args.add_release_to_mix:
                    self.WANTS_TO_ADD_RELEASE_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    if self.args.mix_mode_add_at_pos:
                        self.WANTS_TO_ADD_AT_POS_IN_MIX_MODE = True
                if self.args.copy_mix:
                    self.WANTS_TO_COPY_MIX = True
                    self.WANTS_ONLINE = False
                if self.args.discogs_update:
                    self.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                if self.args.delete_mix:
                    self.WANTS_TO_DELETE_MIX = True
                    self.WANTS_ONLINE = False
                if self.args.bulk_edit:
                    self.WANTS_TO_BULK_EDIT = True
                if self.args.brainz_update:
                    self.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    self.BRAINZ_SEARCH_DETAIL = self.args.brainz_update
                    if self.args.brainz_update > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2
                if self.args.edit_mix:
                    self.WANTS_TO_EDIT_MIX = True
                    self.WANTS_ONLINE = False


        # SUGGEST MODE
        if hasattr(self.args, 'suggest_search'):
            self.WANTS_TO_SUGGEST_SEARCH = True
            log.debug("Entered suggestion mode.")
            if (self.args.suggest_bpm and self.args.suggest_search == "0"
                  and self.args.suggest_key):
                log.debug("Entered key and BPM suggestion report.")
                self.WANTS_SUGGEST_KEY_AND_BPM_REPORT = True
            elif (self.args.suggest_bpm and self.args.suggest_search != "0"
                  and self.args.suggest_key):
                log.error("You can't combine BPM and key with Track-combination report.")
                raise SystemExit(1)
            elif self.args.suggest_bpm and self.args.suggest_search != "0":
                log.error("You can't combine BPM with Track-combination report.")
                raise SystemExit(1)
            elif self.args.suggest_key and self.args.suggest_search != "0":
                log.error("You can't combine key with Track-combination report.")
                raise SystemExit(1)
            elif self.args.suggest_bpm and self.args.suggest_search == "0":
                log.debug("Entered BPM suggestion report.")
                self.WANTS_SUGGEST_BPM_REPORT = True
            elif self.args.suggest_key and self.args.suggest_search == "0":
                log.debug("Entered musical key suggestion report.")
                self.WANTS_SUGGEST_KEY_REPORT = True
            elif self.args.suggest_search == "0":
                log.debug("Entered Track-combination report. No searchterm.")
            else:
                log.debug("Entered Track-combination report.")
                self.WANTS_SUGGEST_TRACK_REPORT = True
            #log.error("track search not implemented yet.")
            #raise SystemExit(1)


        # IMPORT MODE
        if hasattr(self.args, 'import_id'):
            log.debug("Entered import mode.")
            if self.args.import_id != 0 and self.args.import_add_coll:
                self.WANTS_TO_ADD_AND_IMPORT_RELEASE = True
            elif self.args.import_id == 0 and self.args.import_add_coll:
                log.error(
                  "Release ID missing. Which release should we add to collection and import?")
                raise SystemExit(1)
            elif self.args.import_id == 0:
                if self.args.import_tracks:
                    self.WANTS_TO_IMPORT_COLLECTION_WITH_TRACKS = True
                    if self.args.import_offset > 0:
                        self.RESUME_OFFSET = self.args.import_offset
                elif self.args.import_brainz:
                    self.WANTS_TO_IMPORT_COLLECTION_WITH_BRAINZ = True
                    self.BRAINZ_SEARCH_DETAIL = self.args.import_brainz
                    if self.args.import_brainz > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2
                    if self.args.import_offset > 0:
                        self.RESUME_OFFSET = self.args.import_offset
                else:
                    self.WANTS_TO_IMPORT_COLLECTION = True
            else:
                if self.args.import_brainz or self.args.import_tracks:
                    log.error(
                      "You can't combine a single release import with -z or -u.")
                    raise SystemExit(1)
                else:
                    self.WANTS_TO_IMPORT_RELEASE = True


        # SETUP MODE
        if self.args.command == 'setup':
            log.debug("Entered setup mode.")
            self.WANTS_TO_LAUNCH_SETUP = True
            if self.args.force_upgrade_schema == True:
                self.WANTS_TO_FORCE_UPGRADE_SCHEMA = True


        # NO COMMAND - SHOW HELP
        if self.args.command == None:
            self.DID_NOT_PROVIDE_COMMAND = True

        if self.args.offline_mode == True:
            self.WANTS_ONLINE = False

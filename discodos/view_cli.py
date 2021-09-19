import logging
from tabulate import tabulate as tab
#  import pprint
from time import time
from datetime import timedelta
# from collections import OrderedDict

from discodos.view_common import View_common
from discodos.view_common import Mix_view_common, Collection_view_common

log = logging.getLogger('discodos')


class View_common_cli(View_common):
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

    def tab_mix_table(self, _mix_data, _verbose=False, brainz=False):
        _mix_data_key_bpm = self.replace_key_bpm(_mix_data)
        _mix_data_nl = self.trim_table_fields(_mix_data_key_bpm)
        # for row in _mix_data_nl: # debug only
        #    log.debug(str(row))
        # log.debug("")
        if _verbose:
            self.p(tab(
                _mix_data_nl,
                tablefmt='pipe',
                headers=self.cols_mixtracks.headers_dict(short=True)
            ))
        elif brainz:
            _mix_data_brainz = self.replace_brainz(_mix_data_key_bpm)
            _mix_data_brainz_nl = self.trim_table_fields(
                _mix_data_brainz,
                exclude=['methods']
            )
            self.p(tab(
                _mix_data_brainz_nl,
                tablefmt='grid',
                headers=self.headers_dict_mixtracks_brainz
            ))
        else:
            self.p(tab(
                _mix_data_nl,
                tablefmt='pipe',
                headers=self.headers_dict_mixtracks_basic
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


class Mix_view_cli(Mix_view_common, View_common_cli, View_common):
    """ Viewing mixes outputs on CLI.
    """
    def __init__(self):
        super(Mix_view_cli, self).__init__()

    def tab_mixes_list(self, mixes_data):
        mixes_short_timestamps = self.shorten_mixes_timestamps(mixes_data)
        tabulated = tab(
            self.trim_table_fields(mixes_short_timestamps),
            tablefmt="simple",
            headers=self.cols_mixes.headers_dict()  # data is dict, headers too
        )
        self.p(tabulated)

    def tab_mix_info_header(self, mix_info):
        self.p(tab(
            [mix_info],
            tablefmt="plain",
            headers=self.headers_list_mixinfo
        ))

    def really_add_track(self, track_to_add, release_name, mix_id, pos):
        _answ = self.ask(
            'Add "{}" on "{}" to mix #{}, at position {}? (Y/n) '.format(
                track_to_add.upper(),
                release_name,
                int(mix_id), pos)
        )
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


class Collection_view_cli(Collection_view_common, View_common_cli, View_common):
    """ Viewing collection (search) outputs on CLI.
    """
    def __init__(self):
        super(Collection_view_cli, self).__init__()

    def tab_online_search_results(self, _result_list):
        self.p(
            tab(_result_list, tablefmt="simple", headers={
                'id': 'ID', 'artist': 'Artist', 'title': 'Release',
                'label': 'Label', 'country': 'C', 'year': 'Year',
                'format': 'Format'
            }))

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
        self, releases_total, releases_matched, tracks_total, tracks_matched,
        releases_collection_flag, releases_collection_online,
        mixtracks_total, mixtracks_unique
    ):
        stats = [
            ['Releases in DiscoBASE', releases_total],
            ['Releases in Collection (DB flag)', releases_collection_flag],
            ['Releases in Collection (Discogs)', releases_collection_online],
            ['Releases matched with *Brainz', releases_matched],
            ['Tracks in DiscoBASE', tracks_total],
            ['Tracks matched with *Brainz', tracks_matched],
            ['Tracks in mixes', mixtracks_total],
            ['Unique tracks in mixes', mixtracks_unique],
        ]
        self.p(tab(stats, tablefmt='plain'), lead_nl=True)

from discodos.utils import is_number, join_sep
from abc import ABC, abstractmethod
from discodos import log
from tabulate import tabulate as tab # should be only in views.py
import pprint
from datetime import datetime
from datetime import date
from time import time


# common view utils, usable in CLI and GUI
class View_common(ABC):
    def shorten_timestamp(self, sqlite_date, text = False):
        ''' remove time from timestamps we get out of the db, just leave date'''
        date_only = datetime.fromisoformat(sqlite_date).date()
        if text == True:
            return str(date_only)
        return date_only

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
            if row_mutable[keys_list[1]] is None:
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
        if row_mut[keys_list[0]] is None:
            row_mut[keys_list[0]] = "-"
        if row_mut[keys_list[1]] is None:
            row_mut[keys_list[1]] = "-"
        combined_key_bpm = "{}/{}".format(row_mut[keys_list[0]],
              str(row_mut[keys_list[1]]))
        combined_with_space = combined_key_bpm.ljust(set_width)
        #log.warning("Combined string: {}".format(combined_str))
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
                cut_pos_space = False # reset cut_pos_space on each field cycle
                if (not is_number(field) and field is not None
                    and not key in exclude):
                    if len(field) > cut_pos:
                        cut_pos_space = field.find(" ", cut_pos)
                        log.debug("cut_pos_space index (next space after cut_pos): %s", cut_pos_space)
                        # don't edit if no space following (almost at end)
                        if cut_pos_space == -1:
                            edited_field = field
                        else:
                            edited_field = field[0:cut_pos_space] + "\n" + field[cut_pos_space+1:]
                        log.debug("string from 0 to cut_pos_space: {}".format(field[0:cut_pos_space]))
                        log.debug("string from cut_pos_space to end: {}".format(field[cut_pos_space:]))
                        log.debug("the final string:")
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

            links = []
            if row['m_rel_id_override']:
                links.append(self.link_to('musicbrainz release', row['m_rel_id_override']))
            if row['m_rel_id']:
                links.append(self.link_to('musicbrainz release', row['m_rel_id']))
            if row['m_rec_id_override']:
                links.append(self.link_to('musicbrainz recording', row['m_rec_id_override']))
                links.append(self.link_to('acousticbrainz recording', row['m_rec_id_override']))
            elif row['m_rec_id']:
                links.append(self.link_to('musicbrainz recording', row['m_rec_id']))
                links.append(self.link_to('acousticbrainz recording', row['m_rec_id']))
            if row['discogs_id']:
                links.append(self.link_to('discogs release', row['discogs_id']))
            links_str = join_sep(links, '\n')
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
            ["d_release_id", "Release ID ({}): "],
            ["notes", "Other track notes: ({}): "]
        ]

# Collection view utils, usable in CLI and GUI, related to Collection only
class Collection_view_common(ABC):
    def __init__(self):
        #super(Collection_view_cli, self).__init__()
        pass

    def d_tracklist_parse(self, d_tracklist, track_number):
        '''gets Track name from discogs tracklist object via track_number, eg. A1'''
        for tr in d_tracklist:
            #log.debug("d_tracklist_parse: this is the tr object: {}".format(dir(tr)))
            #log.debug("d_tracklist_parse: this is the tr object: {}".format(tr))
            if tr.position == track_number:
                return tr.title
        log.debug('d_tracklist_parse: Track {} not existing on release.'.format(
            track_number))
        return False # we didn't find the tracknumber

    def d_tracklist_parse_numerical(self, d_tracklist, track_number):
        '''get numerical track pos from discogs tracklist object via
           track_number, eg. A1'''
        for num, tr in enumerate(d_tracklist):
            if tr.position == track_number:
                return num + 1 # return human readable (matches brainz position)
        log.debug(
            'd_tracklist_parse_numerical: Track {} not existing on release.'.format(
              track_number))
        return False # we didn't find the tracknumber

# common view utils, usable in CLI only
class View_common_cli(View_common):
    def p(self, message):
        print(''+str(message)+'\n')

    def ask(self, text=""):
        ''' ask user for something and return answer '''
        return input(text)

    def ask_for_track(self):
        track_no = self.ask("Which track? (A1) ")
        # FIXME a sanity checker, at least for online search, would be nice here.
        # also the default value is not checked, eg it could be A in reality!
        if track_no == '':
            track_no = 'A1'
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
        took_str = datetime.fromtimestamp(took_seconds).strftime('%Mm %Ss')
        msg_took = "{} took {}".format(msg, took_str)
        log.info('CTRLS: {} took {} seconds'.format(msg, took_seconds))
        log.info('CTRLS: {}'.format(msg_took))
        print(msg_took)

# viewing mixes in CLI mode:
class Mix_view_cli(Mix_view_common, View_common_cli, View_common):
    def __init__(self):
        super(Mix_view_cli, self).__init__()

    def tab_mixes_list(self, mixes_data):
        # make list of dicts out of the sqlite tuples list
        mixes = [dict(row) for row in mixes_data]
        for i, mix in enumerate(mixes): # shorten all created timestamp fields
            mixes[i]['created'] = self.shorten_timestamp(mix['created'],
                  text = True)
            mixes[i]['played'] = self.format_date_month(mix['played'],
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
            .format(track_to_add, release_name, int(mix_id), pos))
        _answ = self.ask(quest)
        if _answ.lower() == "y" or _answ.lower() == "":
            return True

# viewing collection (search) outputs in CLI mode:
class Collection_view_cli(Collection_view_common, View_common_cli, View_common):
    def __init__(self):
        super(Collection_view_cli, self).__init__()

    def print_found_discogs_release(self, discogs_results, _searchterm, _db_releases):
        ''' formatted output _and return of Discogs release search results'''
        # only show pages count if it's a Release Title Search
        if not is_number(_searchterm):
            self.p("Found "+str(discogs_results.pages )+" page(s) of results!")
        else:
            self.p("ID: "+discogs_results[0].id+", Title: "+discogs_results[0].title+"")
        for result_item in discogs_results:
            self.p("Checking " + str(result_item.id))
            for dbr in _db_releases:
                if result_item.id == dbr[0]:
                    self.p("Good, first matching record in your collection is:")
                    result_list=[]
                    result_list.append([])
                    result_list[0].append(result_item.id)
                    result_list[0].append(str(result_item.artists[0].name))
                    result_list[0].append(result_item.title)
                    result_list[0].append(str(result_item.labels[0].name))
                    result_list[0].append(result_item.country)
                    result_list[0].append(str(result_item.year))
                    #result_list[0].append(str(result_item.formats[0]['descriptions'][0])+
                    #           ", "+str(result_item.formats[0]['descriptions'][1]))
                    result_list[0].append(str(result_item.formats[0]['descriptions'][0])+
                               ", "+str(result_item.formats[0]['descriptions'][0]))

                    self.tab_online_search_results(result_list)
                    self.online_search_results_tracklist(result_item.tracklist)
                    break
            try:
                if result_item.id == dbr[0]:
                    #return result_list[0]
                    log.info("Compiled Discogs result_list: {}".format(result_list))
                    return result_list
                # FIXME this is bullshit, will never be reached FIXME
                #    break
            except UnboundLocalError:
                log.error("Discogs collection was not imported to DiscoBASE properly!")
                #raise unb
                raise SystemExit(1)
        return False

    def tab_online_search_results(self, _result_list):
        self.p(tab(_result_list, tablefmt="simple",
                  headers=["ID", "Artist", "Release", "Label", "C", "Year", "Format"]))

    def online_search_results_tracklist(self, _tracklist):
        for track in _tracklist:
            print(track.position + "\t" + track.title)
        print()

    def tab_all_releases(self, releases_data):
        #self.p(tab(releases_data, tablefmt="plain",
        print(tab(releases_data, tablefmt="plain",
            #headers=["Discogs ID", "Artist", "Release Title", "Last import", "in Collection"]))
            headers=["Discogs ID", "Artist", "Release Title"]))

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

    def brainz_processed_report(self, processed, added_release, added_rec,
      added_key, added_chords_key, added_bpm, errors_db, errors_not_found):
        msg_mb = 'Processed: {}.\nAdded MusicBrainz info to DiscoBASE: '.format(processed)
        msg_mb+= 'Release MBIDs: {}, Recording MBIDs: {}\n'.format(
            added_release, added_rec)
        msg_mb+= 'Added AccousticBrainz info: Key: {}, Chords Key: {}, BPM: {}'.format(
            added_key, added_chords_key, added_bpm)
        msg_err = 'Database errors: {}. Not found on Discogs errors: {}.'.format(
            errors_db, errors_not_found)
        msg_note = 'Note that some of your tracks might be from the same release. '
        msg_note+= 'Thus, the total release count added in reality might be less.'
        print(msg_mb+'\n'+msg_err+'\n\n'+msg_note)
        log.info(msg_mb+'\n'+msg_err+'\n\n'+msg_note)
        print("") # space for readability

        msg1 = "If DiscoDOS didn't find many Release MBIDs or Recording MBIDs "
        msg1+= "and hence no key and BPM data, "
        msg1+= "please investigate: Execute match command again "
        msg1+= "with increased log-level: disco -v .. "
        print(msg1)
        msg2 = "Help improving the matching algorithm: "
        msg2+= "Open an issue on github.com/JOJ0/discodos"
        print(msg2+'\n')


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
        self.WANTS_SUGGEST_BPM_AND_KEY_REPORT = False
        self.WANTS_TO_PULL_BRAINZ_INFO = False
        self.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = False
        self.BRAINZ_SEARCH_DETAIL = 1
        self.WANTS_MUSICBRAINZ_MIX_TRACKLIST = False

        # RELEASE MODE:
        if hasattr(self.args, 'release_search'):
            if "all" in self.args.release_search:
                self.WANTS_TO_LIST_ALL_RELEASES = True
                self.WANTS_ONLINE = False
            else:
                self.WANTS_TO_SEARCH_FOR_RELEASE = True
                if (self.args.add_to_mix != 0 and self.args.track_to_add != 0
                  and self.args.add_at_pos):
                    self.WANTS_TO_ADD_AT_POSITION = True
                if self.args.add_to_mix !=0 and self.args.track_to_add !=0:
                    self.WANTS_TO_ADD_TO_MIX = True
                if self.args.add_to_mix !=0:
                    self.WANTS_TO_ADD_TO_MIX = True

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
                if self.args.brainz_update:
                    self.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE = True
                    self.WANTS_ONLINE = True
                    self.BRAINZ_SEARCH_DETAIL == self.args.brainz_update
                    if self.args.brainz_update > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2
            else:
                self.WANTS_TO_SHOW_MIX_TRACKLIST = True
                self.WANTS_ONLINE = False
                #if hasattr(self.args, 'create_mix')
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
                    self.BRAINZ_SEARCH_DETAIL == self.args.brainz_update
                    if self.args.brainz_update > 1:
                        self.BRAINZ_SEARCH_DETAIL = 2


        # SUGGEST MODE
        if hasattr(self.args, 'suggest_search'):
            self.WANTS_TO_SUGGEST_SEARCH = True
            log.debug("Entered suggestion mode.")
            if (self.args.suggest_bpm and self.args.suggest_search == "0"
                  and self.args.suggest_key):
                log.debug("Entered BPM and key suggestion report.")
                self.WANTS_SUGGEST_BPM_AND_KEY_REPORT = True
            elif (self.args.suggest_bpm and self.args.suggest_search is not "0"
                  and self.args.suggest_key):
                log.error("You can't combine BPM and key with Track-combination report.")
                raise SystemExit(1)
            elif self.args.suggest_bpm and self.args.suggest_search is not "0":
                log.error("You can't combine BPM with Track-combination report.")
                raise SystemExit(1)
            elif self.args.suggest_key and self.args.suggest_search is not "0":
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

        if self.args.offline_mode == True:
            self.WANTS_ONLINE = False

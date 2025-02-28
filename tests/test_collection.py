from datetime import datetime
import inspect
import os
import unittest
from pathlib import Path
from shutil import copy2
from sqlite3 import Row
from unittest.mock import Mock

from discodos.config import Config
from discodos.model import Collection


class TestCollection(unittest.TestCase):
    """Tests collection DiscoBASE model methods."""
    @classmethod
    def setUpClass(cls):
        name = inspect.currentframe().f_code.co_name
        cls.clname = cls.__name__  # Classname, used in test output
        print("\n{} - {} - BEGIN".format(cls.clname, name))
        # log.handlers[0].setLevel("INFO")  # handler 0 is the console handler
        # log.handlers[0].setLevel("DEBUG")  # handler 0 is the console handler
        cls.conf = Config()  # doesn't get path of test-db, so...
        discodos_tests = Path(os.path.dirname(os.path.abspath(__file__)))
        empty_db_path = discodos_tests / 'fixtures' / 'discobase_empty.db'
        cls.db_path = discodos_tests / 'discobase.db'
        print('Database: {}'.format(copy2(empty_db_path, cls.db_path)))
        print("{} - {} - END\n".format(cls.clname, name))

    def debug_db(self, db_return):
        # print(db_return.keys())
        print()
        if isinstance(db_return, list):
            print('db_return is a list')
            for i in db_return:
                stringed = ''
                for j in i:
                    stringed+='{}, '.format(j)
                print(stringed)
                print()
        elif isinstance(db_return, Row):
            print('db_return is a Row')
            stringed = ''
            for i in db_return:
                stringed+='{}, '.format(i)
            print(stringed)
            print()
        else:
            print("Neither list nor Row, just print:")
            print(db_return)
        return True

    def test_get_all_db_releases(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        # instantiate the Collection model class
        collection = Collection(False, self.db_path)
        db_return = collection.get_all_db_releases()
        # self.debug_db(db_return)
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 4)
        self.assertEqual(db_return[2]['discogs_id'], 123456)
        self.assertEqual(db_return[2]['discogs_title'], 'Material Love')
        # self.assertEqual(db_return[2]['import_timestamp'], '2020-01-25 22:33:35')
        self.assertEqual(db_return[2]['d_artist'], 'Märtini Brös.')
        # self.assertEqual(db_return[2]['in_d_collection'], 1)
        self.assertEqual(db_return[3]['discogs_id'], 8620643)
        self.assertEqual(db_return[3]['discogs_title'], 'The Crane')
        # self.assertEqual(db_return[3]['import_timestamp'], '2020-01-30 10:06:26')
        self.assertEqual(db_return[3]['d_artist'], 'Source Direct')
        # self.assertEqual(db_return[3]['in_d_collection'], 1)
        print("{} - {} - END".format(self.clname, name))

    def test_get_release_by_id(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        # instantiate the Collection model class
        collection = Collection(False, self.db_path)
        db_return = collection.get_release_by_id('123456')
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 10)  # should be 10 columns
        self.assertEqual(db_return['discogs_id'], 123456)
        self.assertEqual(db_return['d_artist'], 'Märtini Brös.')
        self.assertEqual(db_return['discogs_title'], 'Material Love')
        print("{} - {} - END".format(self.clname, name))

    def test_search_release_offline_number(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.search_release_offline('123456')
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 10)  # should be 10 columns
        self.assertEqual(db_return['discogs_id'], 123456)
        self.assertEqual(db_return['d_artist'], 'Märtini Brös.')
        self.assertEqual(db_return['discogs_title'], 'Material Love')
        print("{} - {} - END".format(self.clname, name))

    def test_search_release_offline_number_error(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.search_release_offline('999999')
        self.assertIsNone(db_return)
        print("{} - {} - END".format(self.clname, name))

    def test_search_release_offline_text(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.search_release_offline('Märtini')  # artist or title
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 1)  # should be a list with 1 Row
        self.assertEqual(db_return[0]['discogs_id'], 123456)
        self.assertEqual(db_return[0]['d_artist'], 'Märtini Brös.')
        self.assertEqual(db_return[0]['discogs_title'], 'Material Love')
        print("{} - {} - END".format(self.clname, name))

    def test_search_release_offline_text_multiple(self):
        print("\nTestMix.search_release_offline_text_multiple: BEGIN")
        collection = Collection(False, self.db_path)
        db_return = collection.search_release_offline('Amon')  # artist or title
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 2)  # should be a list with 2 Rows
        self.assertEqual(db_return[0]['discogs_id'], 69092)
        self.assertEqual(db_return[0]['d_artist'], 'Amon Tobin')
        self.assertEqual(db_return[0]['discogs_title'], 'Out From Out Where')
        self.assertEqual(db_return[1]['discogs_id'], 919698)
        self.assertEqual(db_return[1]['d_artist'], 'Amon Tobin')
        self.assertEqual(db_return[1]['discogs_title'], 'Foley Room')
        print("TestMix.search_release_offline_text_multiple: DONE\n")

    def test_search_release_offline_text_error(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.search_release_offline('XXX')  # artist or title
        self.assertIsNone(db_return)  # returns None if nothing found
        # self.assertEqual(db_return, [])  # FIXME should this better be empty list?
        print("{} - {} - END".format(self.clname, name))

    def test_get_tracks_by_bpm(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.get_tracks_by_bpm(125, 6)
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 3)  # should be a list with 3 Rows
        self.assertEqual(db_return[0]['d_artist'], 'Source Direct')
        self.assertEqual(db_return[0]['d_track_no'], 'AA')
        self.assertEqual(db_return[0]['chosen_bpm'], 120)
        self.assertEqual(db_return[1]['d_artist'], 'Märtini Brös.')
        self.assertEqual(db_return[1]['d_track_no'], 'A1')
        self.assertEqual(db_return[1]['chosen_bpm'], 125)
        self.assertEqual(db_return[2]['d_artist'], 'Märtini Brös.')
        self.assertEqual(db_return[2]['d_track_no'], 'B2')
        self.assertEqual(db_return[2]['chosen_bpm'], 130)
        print("{} - {} - END".format(self.clname, name))

    def test_get_tracks_by_key(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.get_tracks_by_key("Am")
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 2)  # should be a list with 2 Rows
        self.assertEqual(db_return[0]['d_artist'], 'Source Direct')
        self.assertEqual(db_return[0]['d_track_no'], 'AA')
        self.assertEqual(db_return[0]['chosen_bpm'], 120)
        self.assertEqual(db_return[1]['d_artist'], 'Märtini Brös.')
        self.assertEqual(db_return[1]['d_track_no'], 'A1')
        self.assertEqual(db_return[1]['chosen_bpm'], 125)
        print("{} - {} - END".format(self.clname, name))

    def test_search_release_track_offline_artist(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        dbr = collection.search_release_track_offline(
            artist='Märtini', release='', track='')
        # self.debug_db(dbr)
        self.assertIsNotNone(dbr)
        self.assertEqual(len(dbr), 3)  # should be a list with 3 Rows
        self.assertEqual(dbr[2]['discogs_id'], 123456)
        self.assertEqual(dbr[0]['d_artist'], 'Märtini Brös.')
        self.assertEqual(dbr[1]['discogs_title'], 'Material Love')
        print("{} - {} - END".format(self.clname, name))

    def test_search_release_track_offline_nothing(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        dbr = collection.search_release_track_offline(
            artist='', release='', track='')
        # self.debug_db(dbr)
        self.assertIsNotNone(dbr)
        self.assertEqual(len(dbr), 0)  # should be a list with 0 Rows
        print("{} - {} - END".format(self.clname, name))

    # Since we changed artist field from release to track table this test is
    # broken, not sure if we ever go back to old behaviour we had in guiv1draft
    # (a discobase without fully imported tracks should even show a release that
    # when no corresponding tracks are found in the tracks table.)
    # def test_search_release_track_offline_artist_without_tracks(self):
    #    name = inspect.currentframe().f_code.co_name
    #    print("\n{} - {} - BEGIN".format(self.clname, name))
    #    collection = Collection(False, self.db_path)
    #    dbr = collection.search_release_track_offline(
    #        artist='Amon', release='', track='')
    #    #self.debug_db(dbr)
    #    self.assertIsNotNone(dbr)
    #    self.assertEqual(len(dbr), 2)  # should be a list with 2 Rows
    #    self.assertEqual(dbr[0]['d_artist'], 'Amon Tobin')
    #    self.assertEqual(dbr[0]['discogs_title'], 'Foley Room')
    #    self.assertEqual(dbr[0]['d_artist'], 'Amon Tobin')
    #    self.assertEqual(dbr[1]['discogs_title'], 'Out From Out Where')
    #    print("{} - {} - END".format(self.clname, name))

    def test_search_release_track_offline_track(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        dbr = collection.search_release_track_offline(
            artist='', release='', track='Hedup!')
        # self.debug_db(dbr)
        self.assertIsNotNone(dbr)
        self.assertEqual(len(dbr), 1)  # should be a list with 1 Rows
        self.assertEqual(dbr[0]['d_artist'], 'Märtini Brös.')
        self.assertEqual(dbr[0]['discogs_title'], 'Material Love')
        self.assertEqual(dbr[0]['d_track_name'], 'Hedup!')
        print("{} - {} - END".format(self.clname, name))

    def test_search_release_track_offline_release(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        dbr = collection.search_release_track_offline(
            artist='', release='material', track='')
        # self.debug_db(dbr)
        self.assertIsNotNone(dbr)
        self.assertEqual(len(dbr), 3)  # it's one release but finds all track entries!
        self.assertEqual(dbr[0]['d_artist'], 'Märtini Brös.')
        self.assertEqual(dbr[1]['d_track_name'], 'Material Love')
        self.assertEqual(dbr[2]['discogs_title'], 'Material Love')
        print("{} - {} - END".format(self.clname, name))

    def test_search_release_track_offline_artist_release_track(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        dbr = collection.search_release_track_offline(
            artist='Märtini', release='material', track='cab')
        # self.debug_db(dbr)
        self.assertIsNotNone(dbr)
        self.assertEqual(len(dbr), 1)  # one track
        self.assertEqual(dbr[0]['d_artist'], 'Märtini Brös.')
        self.assertEqual(dbr[0]['d_track_name'], 'Material Love (Cab Drivers Remix)')
        self.assertEqual(dbr[0]['discogs_title'], 'Material Love')
        print("{} - {} - END".format(self.clname, name))

    def test_track_report_snippet(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.track_report_snippet(4, 133)
        self.assertEqual(len(db_return), 3)  # a snippet is always 3 tracks
        # track 3
        self.assertEqual(db_return[0]["track_pos"], 3)
        self.assertEqual(db_return[0]["discogs_title"], "Material Love")
        self.assertEqual(db_return[0]["d_track_no"], "B1")
        self.assertEqual(db_return[0]["trans_rating"], "")
        self.assertEqual(db_return[0]["key"], None)
        self.assertEqual(db_return[0]["bpm"], 140)
        self.assertEqual(db_return[0]["a_key"], None)
        self.assertEqual(db_return[0]["a_bpm"], None)
        # track 4
        self.assertEqual(db_return[1]["track_pos"], 4)
        self.assertEqual(db_return[1]["discogs_title"], "The Crane")
        self.assertEqual(db_return[1]["d_track_no"], "AA")
        self.assertEqual(db_return[1]["trans_rating"], "")
        self.assertEqual(db_return[1]["key"], "Am")
        self.assertEqual(db_return[1]["bpm"], 120)
        self.assertEqual(db_return[1]["a_key"], None)
        self.assertEqual(db_return[1]["a_bpm"], None)
        # track 5
        self.assertEqual(db_return[2]["track_pos"], 5)
        print("{} - {} - END".format(self.clname, name))

    def test_track_report_occurences(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.track_report_occurences(123456, 'B2')
        self.assertEqual(len(db_return), 11)  # track was used 11 times
        # check some occurences
        self.assertEqual(db_return[0]["mix_id"], 125)  # first occurence
        self.assertEqual(db_return[0]["track_pos"], 2)  # used at pos 2
        self.assertEqual(
            db_return[0]["name"],
            'test 125 last_tr, tr_of_one_mix, one_mix')
        self.assertEqual(db_return[7]["mix_id"], 132)  # 8th occurence
        self.assertEqual(db_return[7]["track_pos"], 2)  # used at pos 2
        self.assertEqual(db_return[10]["mix_id"], 135)  # 11th occurence
        self.assertEqual(db_return[10]["track_pos"], 2)  # used at pos 2
        print("{} - {} - END".format(self.clname, name))

    def test_stats_match_method_release(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_match_method_release()
        # self.debug_db(db_return)
        self.assertEqual(len(db_return), 3)  # should be a list with 4 Rows
        self.assertEqual(db_return[0]['m_match_method'], None)
        self.assertEqual(db_return[1]['m_match_method'], 'CatNo (exact)')
        self.assertEqual(db_return[2]['m_match_method'], "Discogs URL")
        print("{} - {} - END".format(self.clname, name))

    def test_d_get_first_catno(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        label_item = Mock()  # Mock a label object.
        label_item.data = {'catno': 'ZEN 70'}
        mock_d_labels = [label_item]  # Mock list of label objects.
        catno = collection.d_get_first_catno(  # And finally test.
            mock_d_labels
        )
        self.assertEqual(catno, 'ZEN 70')
        print("{} - {} - END".format(self.clname, name))

    def test_stats_releases_total(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_releases_total()
        # self.debug_db(db_return)
        self.assertEqual(db_return, 4)  # should be 4 releases in coll.
        print("{} - {} - END".format(self.clname, name))

    def test_stats_tracks_total(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_tracks_total()
        # self.debug_db(db_return)
        self.assertEqual(db_return, 5)  # should be 5 tracks in coll.
        print("{} - {} - END".format(self.clname, name))

    def test_stats_tracks_total_ext(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_tracks_total_ext()
        # self.debug_db(db_return)
        self.assertEqual(db_return, 5)  # should be 5 tracks in track_ext t.
        print("{} - {} - END".format(self.clname, name))

    def test_stats_track_ext_orphaned(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_track_ext_orphaned()
        # self.debug_db(db_return)
        self.assertEqual(db_return, 0)
        print("{} - {} - END".format(self.clname, name))

    def test_stats_releases_matched(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_releases_matched()
        self.assertEqual(db_return, 2)  # should be 2 matched releases
        print("{} - {} - END".format(self.clname, name))

    def test_stats_tracks_matched(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_tracks_matched()
        self.assertEqual(db_return, 1)  # should be 1 matched tracks
        print("{} - {} - END".format(self.clname, name))

    def test_stats_releases_d_collection_flag(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_collection_items_discobase()
        self.assertEqual(db_return, 4)
        print("{} - {} - END".format(self.clname, name))

    def test_stats_mixtracks_total(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_mixtracks_total()
        # self.debug_db(db_return)
        self.assertEqual(db_return, 49)
        print("{} - {} - END".format(self.clname, name))

    def test_stats_mixtracks_unique(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_mixtracks_unique()
        # self.debug_db(db_return)
        self.assertEqual(db_return, 7)  # 7 unique tracks
        print("{} - {} - END".format(self.clname, name))

    def test_stats_tracks_key_brainz(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_tracks_key_brainz()
        self.assertEqual(db_return, 1)  # should be 1 track with ab_key
        print("{} - {} - END".format(self.clname, name))

    def test_stats_tracks_key_manual(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_tracks_key_manual()
        self.assertEqual(db_return, 4)  # should be 4 tracks with manual key
        print("{} - {} - END".format(self.clname, name))

    def test_stats_tracks_bpm_brainz(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_tracks_bpm_brainz()
        self.assertEqual(db_return, 1)  # should be 1 track with ab_bpm
        print("{} - {} - END".format(self.clname, name))

    def test_stats_tracks_bpm_manual(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.stats_tracks_bpm_manual()
        self.assertEqual(db_return, 5)  # should be 5 tracks with manual bpm
        print("{} - {} - END".format(self.clname, name))

    def test_set_collection_item_folder(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.set_collection_item_folder(
            instance_id=26575804,
            folder_id=123,
            sold_folder_id=456,
            timestamp="2025-02-28 07:29:56",
        )
        self.assertEqual(db_return, 1)
        print("{} - {} - END".format(self.clname, name))

    def test_set_collection_item_folder_misconfigured_str(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.set_collection_item_folder(
            instance_id=26575804,
            folder_id=1,
            sold_folder_id="abc",
            timestamp="2025-02-28 07:29:56",
        )
        self.assertEqual(db_return, 1)
        print("{} - {} - END".format(self.clname, name))

    def test_set_collection_item_folder_misconfigured_emtpy_str(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        collection = Collection(False, self.db_path)
        db_return = collection.set_collection_item_folder(
            instance_id=26575804,
            folder_id=1,
            sold_folder_id="",
            timestamp="2025-02-28 07:29:56",
        )
        self.assertEqual(db_return, 1)
        print("{} - {} - END".format(self.clname, name))

    @classmethod
    def tearDownClass(cls):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(cls.clname, name))
        os.remove(cls.db_path)
        print("{} - {} - END\n".format(cls.clname, name))


if __name__ == '__main__':
    loader = unittest.TestLoader()
    ln = lambda f: getattr(TestCollection, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    loader.sortTestMethodsUsing = lncmp
    unittest.main(testLoader=loader, verbosity=2)

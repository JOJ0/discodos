import inspect
import os
import unittest
from pathlib import Path
from shutil import copy2

# from discodos.config import Config
from discodos.model import Mix  # , log


class TestMix(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # log.handlers[0].setLevel("INFO")  # handler 0 is the console handler
        # log.handlers[0].setLevel("DEBUG")  # handler 0 is the console handler
        discodos_tests = Path(os.path.dirname(os.path.abspath(__file__)))
        empty_db_path = discodos_tests / 'fixtures' / 'discobase_empty.db'
        self.db_path = discodos_tests / 'discobase.db'
        self.clname = self.__name__   # just handy a shortcut, used in test output
        print('TestMix.setUpClass: test-db: {}'.format(
            copy2(empty_db_path, self.db_path)))
        print("TestMix.setUpClass: done\n")

    def test_non_existent(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        # instantiate the Mix model class (empty, mix 123 = non-existent)
        self.mix = Mix(False, 123, self.db_path)
        self.assertFalse(self.mix.id_existing)
        print("{} - {} - END".format(self.clname, name))

    def test_create(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 123, self.db_path)
        db_return = self.mix.create("2020-01-01", "test venue", "test mix 1")
        self.assertEqual(db_return, 1)
        self.assertTrue(self.mix.id_existing)
        self.assertTrue(self.mix.name_existing)
        self.assertEqual(self.mix.name, "test mix 1")
        self.assertEqual(self.mix.venue, "test venue")
        self.assertEqual(self.mix.played, "2020-01-01")
        print("{} - {} - END".format(self.clname, name))

    def test_delete(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 124, self.db_path)
        db_return = self.mix.delete()
        self.assertEqual(db_return, 1)
        self.assertFalse(self.mix.id_existing)
        self.assertFalse(self.mix.name_existing)
        # self.mix.name is kept for user help output
        self.assertFalse(self.mix.venue)
        self.assertFalse(self.mix.played)
        print("{} - {} - END".format(self.clname, name))

    def test_get_one_mix_track(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 125, self.db_path)
        db_return = self.mix.get_one_mix_track(2)  # get track #2
        self.assertEqual(len(db_return), 13)  # select returns 13 cols
        self.assertEqual(db_return["track_pos"], 2)
        self.assertEqual(db_return["discogs_title"], "Material Love")
        self.assertEqual(db_return["d_track_name"], "Hedup!")
        self.assertEqual(db_return["d_track_no"], "B2")
        self.assertEqual(db_return["trans_rating"], "++++")
        self.assertEqual(db_return["trans_notes"], "test trans 4")
        self.assertEqual(db_return["key"], "C")
        self.assertEqual(db_return["key_notes"], "test key note B2")
        self.assertEqual(db_return["bpm"], 130)
        self.assertEqual(db_return["notes"], "test note B2")
        # how would I test this? db_return["mix_track_id"], "")
        self.assertEqual(db_return["d_release_id"], 123456)
        print("{} - {} - END".format(self.clname, name))

    def test_get_tracks_of_one_mix(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 125, self.db_path)
        db_return = self.mix.get_tracks_of_one_mix()
        self.assertEqual(len(db_return), 2)
        self.assertEqual(db_return[0]["mix_id"], 125)
        self.assertEqual(db_return[0]["d_release_id"], 123456)
        self.assertEqual(db_return[0]["d_track_no"], "A1")
        self.assertEqual(db_return[1]["mix_id"], 125)
        self.assertEqual(db_return[1]["d_release_id"], 123456)
        self.assertEqual(db_return[1]["d_track_no"], "B2")
        print("{} - {} - END".format(self.clname, name))

    def test_get_all_tracks_in_mixes(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 0, self.db_path)
        db_return = self.mix.get_all_tracks_in_mixes()
        # self.assertEqual(len(db_return), 4)  # this will vary if we add tracks, screw it
        self.assertEqual(db_return[0]["mix_id"], 125)
        self.assertEqual(db_return[0]["d_release_id"], 123456)
        self.assertEqual(db_return[0]["d_track_no"], "A1")
        self.assertEqual(db_return[3]["mix_id"], 126)
        self.assertEqual(db_return[3]["d_release_id"], 123456)
        self.assertEqual(db_return[3]["d_track_no"], "B2")
        print("{} - {} - END".format(self.clname, name))

    def test_get_mix_info(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 126, self.db_path)
        db_return = self.mix.get_mix_info()
        self.assertEqual(len(db_return), 6)
        self.assertTrue(self.mix.id_existing)
        self.assertTrue(self.mix.name_existing)
        self.assertEqual(self.mix.name, "test 126 mix_info")
        self.assertEqual(self.mix.venue, "test venue")
        self.assertEqual(self.mix.played, "2020-01-01")
        print("{} - {} - END".format(self.clname, name))

    def test_get_mix_info_error(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 123, self.db_path)  # mix 123 is not existing
        db_return = self.mix.get_mix_info()  # actually this was called in init already
        self.assertEqual(db_return, None)  # _select returns NoneType
        self.assertFalse(self.mix.id_existing)
        self.assertFalse(self.mix.name_existing)
        self.assertEqual(self.mix.name, False)
        self.assertEqual(self.mix.venue, False)
        self.assertEqual(self.mix.played, False)
        print("{} - {} - END".format(self.clname, name))

    def test_get_last_track(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 125, self.db_path)
        db_return = self.mix.get_last_track()
        self.assertEqual(len(db_return), 1)
        # self.assertEqual(db_return["track_pos"], 2)  # no named cols in this case?
        self.assertEqual(db_return[0], 2)  # maybe we use like this somewhere
        print("{} - {} - END".format(self.clname, name))

    def test_add_track(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 127, self.db_path)
        db_ret_add = self.mix.add_track("123456", "B2", 5, 'üüü', '@@@')
        self.assertEqual(db_ret_add, 1)
        db_return = self.mix.get_one_mix_track(5)  # get track #2
        self.assertEqual(len(db_return), 13)  # select returns 13 cols
        self.assertEqual(db_return["track_pos"], 5)
        self.assertEqual(db_return["discogs_title"], "Material Love")
        self.assertEqual(db_return["d_track_name"], "Hedup!")
        self.assertEqual(db_return["d_track_no"], "B2")
        self.assertEqual(db_return["trans_rating"], "üüü")
        self.assertEqual(db_return["trans_notes"], "@@@")
        self.assertEqual(db_return["key"], "C")
        self.assertEqual(db_return["bpm"], 130)
        print("{} - {} - END".format(self.clname, name))

    def test_delete_track(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 128, self.db_path)
        db_ret_del = self.mix.delete_track(3)
        self.assertEqual(db_ret_del, 1)
        db_return = self.mix.get_one_mix_track(3)  # get the track we just deleted
        self.assertEqual(db_return, None)  # select should return nothing aka None
        print("{} - {} - END".format(self.clname, name))

    def test_reorder_tracks(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 129, self.db_path)  # mix 129 is missing track_pos 5
        db_ret_reord = self.mix.reorder_tracks(4)  # reorder starts at pos 4
        self.assertEqual(db_ret_reord, 1)
        db_get_ret = self.mix.get_one_mix_track(5)  # get the track_pos that was the gap
        self.assertEqual(len(db_get_ret), 13)  # select should return 13 columns
        self.assertEqual(
            db_get_ret['d_track_name'],
            'Material Love (Cab Drivers Remix)')  # pos 5 should be this track now
        print("{} - {} - END".format(self.clname, name))

    def test_reorder_tracks_squeeze_in(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 130, self.db_path)  # mix 130 has contains 6 tracks
        # get tracks to shift
        tracks_to_shift = self.mix.get_tracks_from_position(3)  # track 3 is Material Love
        # add new track
        rowcount = self.mix.add_track(8620643, "A", track_pos=3)  # add "The Crane"
        self.assertEqual(rowcount, 1)  # 1 row was added?
        # now shift previously found tracks, shifting starts at pos 3
        db_ret_reord = self.mix.reorder_tracks_squeeze_in(3, tracks_to_shift)
        self.assertEqual(db_ret_reord, 1)
        db_get_crane = self.mix.get_one_mix_track(3)  # get the squeezed in track
        self.assertEqual(len(db_get_crane), 13)  # select should return 13 columns
        self.assertEqual(db_get_crane['d_track_name'], 'The Crane')  # should be The Crane
        db_get_cab = self.mix.get_one_mix_track(4)  # get track after that
        self.assertEqual(len(db_get_cab), 13)  # select should return 13 columns
        self.assertEqual(
            db_get_cab['d_track_name'],
            'Material Love (Cab Drivers Remix)')  # should be cab driver remix
        print("{} - {} - END".format(self.clname, name))

    def test_get_tracks_from_position(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 131, self.db_path)
        db_return = self.mix.get_tracks_from_position(4)
        self.assertEqual(len(db_return), 2)  # should be 2 rows/tracks
        self.assertEqual(db_return[0]['track_pos'], 4)  # first row should be pos 4
        self.assertEqual(db_return[1]['track_pos'], 5)  # second row should be pos 5
        print("{} - {} - END".format(self.clname, name))

    def test_update_mix_track_and_track_ext(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 132, self.db_path)  # instantiate mix 132
        # before edit:
        db_get_bef = self.mix.get_one_mix_track(4)  # get a track
        self.assertEqual(len(db_get_bef), 13)  # select should return 13 columns
        self.assertEqual(
            db_get_bef['d_track_name'],
            'The Crane (Inland & Function Rmx)')  # we won't/can't edit this
        self.assertEqual(db_get_bef['bpm'], 120)  # will be changed
        self.assertEqual(db_get_bef['key'], "Am")  # will be changed
        # do the edit
        track_details = db_get_bef
        edit_answers = {'bpm': 130, 'key': 'Fm'}
        db_ret_upd = self.mix.update_mix_track_and_track_ext(track_details, edit_answers)
        self.assertEqual(db_ret_upd, 1)  # was a row updated?
        # after edit:
        db_get_aft = self.mix.get_one_mix_track(4)  # get the updated track
        self.assertEqual(len(db_get_aft), 13)  # select should return 13 columns
        self.assertEqual(
            db_get_bef['d_track_name'],
            'The Crane (Inland & Function Rmx)')  # we didn't edit this
        self.assertEqual(db_get_aft['bpm'], 130)  # we just changed this
        self.assertEqual(db_get_aft['key'], "Fm")  # we just changed this
        print("{} - {} - END".format(self.clname, name))

    def test_get_full_mix(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 133, self.db_path)
        db_return = self.mix.get_full_mix()  # non-verbose select - not all fields
        self.assertEqual(len(db_return), 7)  # mix 133 contains 7 tracks
        # track 1
        self.assertEqual(db_return[0]["track_pos"], 1)
        self.assertEqual(db_return[0]["discogs_title"], "Material Love")
        self.assertEqual(db_return[0]["d_track_no"], "A1")
        self.assertEqual(db_return[0]["trans_rating"], "+")
        self.assertEqual(db_return[0]["key"], "Am")
        self.assertEqual(db_return[0]["bpm"], 125)
        # track 4
        self.assertEqual(db_return[3]["track_pos"], 4)
        self.assertEqual(db_return[3]["discogs_title"], "The Crane")
        self.assertEqual(db_return[3]["d_track_no"], "AA")
        self.assertEqual(db_return[3]["trans_rating"], "")
        self.assertEqual(db_return[3]["key"], "Am")
        self.assertEqual(db_return[3]["bpm"], 120)
        print("{} - {} - END".format(self.clname, name))

    def test_get_full_mix_verbose(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 133, self.db_path)
        db_return = self.mix.get_full_mix(verbose=True)  # verbose select - all fields
        self.assertEqual(len(db_return), 7)  # mix 133 contains 7 tracks
        # track 1
        self.assertEqual(db_return[0]["track_pos"], 1)
        self.assertEqual(db_return[0]["discogs_title"], "Material Love")
        self.assertEqual(db_return[0]["d_artist"], "Märtini Brös.")
        self.assertEqual(db_return[0]["d_track_name"], "Material Love")
        self.assertEqual(db_return[0]["d_track_no"], "A1")
        self.assertEqual(db_return[0]["key"], "Am")
        self.assertEqual(db_return[0]["bpm"], 125)
        self.assertEqual(db_return[0]["key_notes"], "test key note A1")
        self.assertEqual(db_return[0]["trans_rating"], "+")
        self.assertEqual(db_return[0]["trans_notes"], "test trans 1")
        self.assertEqual(db_return[0]["notes"], "test track note")
        # track 4
        self.assertEqual(db_return[3]["track_pos"], 4)
        self.assertEqual(db_return[3]["discogs_title"], "The Crane")
        self.assertEqual(db_return[3]["d_track_name"], "The Crane (Inland & Function Rmx)")
        self.assertEqual(db_return[3]["d_track_no"], "AA")
        self.assertEqual(db_return[3]["key"], "Am")
        self.assertEqual(db_return[3]["bpm"], 120)
        self.assertEqual(db_return[3]["key_notes"], None)
        self.assertEqual(db_return[3]["trans_rating"], "")
        self.assertEqual(db_return[3]["trans_notes"], "")
        self.assertEqual(db_return[3]["notes"], None)
        print("{} - {} - END".format(self.clname, name))

    def test_get_mix_id_number(self):  # trying to get id from name, but it's an ID
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 0, self.db_path)  # initiate an empty mix
        db_return = self.mix._get_mix_id(125)
        self.assertEqual(db_return, 125)  # should be 125, it's not a name
        print("{} - {} - END".format(self.clname, name))

    def test_get_mix_id_non_existent(self):  # trying to get id from name, but it's unknown
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 0, self.db_path)  # initiate an empty mix
        db_return = self.mix._get_mix_id("unknown mix name")
        self.assertEqual(db_return, None)  # should be None, it's not a known mix name
        print("{} - {} - END".format(self.clname, name))

    def test_get_mix_id(self):  # trying to get id from name
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 0, self.db_path)  # initiate an empty mix
        db_return = self.mix._get_mix_id("test 125")  # real name in db much longer (%?%)
        self.assertEqual(len(db_return), 1)  # should be 1 column
        self.assertEqual(db_return["mix_id"], 125)  # should be ID 125
        print("{} - {} - END".format(self.clname, name))

    def test_shift_track_up(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 134, self.db_path)
        shift_return = self.mix.shift_track(4, 'up')
        self.assertTrue(shift_return)  # should be True
        get_3_return = self.mix.get_one_mix_track(3)
        get_4_return = self.mix.get_one_mix_track(4)
        get_5_return = self.mix.get_one_mix_track(5)  # should stay the same
        self.assertEqual(get_3_return["discogs_title"], 'The Crane')  # Release
        self.assertEqual(get_3_return["d_track_no"], 'AA')  # should be AA
        self.assertEqual(get_4_return["discogs_title"], 'Material Love')  # Release
        self.assertEqual(get_4_return["d_track_no"], 'B1')  # should be AA
        self.assertEqual(get_5_return["discogs_title"], 'Material Love')  # Release
        self.assertEqual(get_5_return["d_track_no"], 'B1')  # should be AA
        print("{} - {} - END".format(self.clname, name))

    def test_shift_track_down(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.mix = Mix(False, 135, self.db_path)
        shift_return = self.mix.shift_track(4, 'down')
        self.assertTrue(shift_return)  # should be True
        get_3_return = self.mix.get_one_mix_track(3)  # should stay the same
        get_4_return = self.mix.get_one_mix_track(4)
        get_5_return = self.mix.get_one_mix_track(5)
        self.assertEqual(get_3_return["discogs_title"], 'Material Love')
        self.assertEqual(get_3_return["d_track_no"], 'B1')
        self.assertEqual(get_4_return["discogs_title"], 'Material Love')
        self.assertEqual(get_4_return["d_track_no"], 'B1')
        self.assertEqual(get_5_return["discogs_title"], 'The Crane')
        self.assertEqual(get_5_return["d_track_no"], 'AA')
        print("{} - {} - END".format(self.clname, name))


    @classmethod
    def tearDownClass(self):
        os.remove(self.db_path)
        print("\nTestMix.teardownClass: done")


if __name__ == '__main__':
    loader = unittest.TestLoader()
    ln = lambda f: getattr(TestMix, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    loader.sortTestMethodsUsing = lncmp
    unittest.main(testLoader=loader, verbosity=2)

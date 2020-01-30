#!/usr/bin/env python
import unittest
from shutil import copy2
from os import remove
from discodos.models import *
from discodos.utils import *


class TestMix(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        log.handlers[0].setLevel("INFO") # handler 0 is the console handler
        #log.handlers[0].setLevel("DEBUG") # handler 0 is the console handler
        conf = Config() # doesn't get path of test-db, so...
        empty_db_path = conf.discodos_root / 'tests' / 'fixtures' / 'discobase_empty.db'
        self.db_path = conf.discodos_root / 'tests' / 'discobase.db'
        print('TestMix.setUpClass: test-db: {}'.format(copy2(empty_db_path, self.db_path)))
        print("TestMix.setUpClass: done\n")

    def test_non_existent(self):
        print("\nTestMix.non_existent: BEGIN")
        # instantiate the Mix model class (empty, mix 123 = non-existent)
        self.mix = Mix(False, 123, self.db_path) 
        self.assertFalse(self.mix.id_existing)
        print("TestMix.non_existent: DONE\n")

    def test_create(self):
        print("\nTestMix.create: BEGIN")
        self.mix = Mix(False, 123, self.db_path) 
        db_return = self.mix.create("2020-01-01", "test venue", "test mix 1")
        self.assertEqual(db_return, 1)
        self.assertTrue(self.mix.id_existing)
        self.assertTrue(self.mix.name_existing)
        self.assertEqual(self.mix.name, "test mix 1")
        self.assertEqual(self.mix.venue, "test venue")
        self.assertEqual(self.mix.played, "2020-01-01")
        print("TestMix.create: DONE\n")

    def test_delete(self):
        print("\nTestMix.delete: BEGIN")
        self.mix = Mix(False, 124, self.db_path)
        db_return = self.mix.delete()
        self.assertEqual(db_return, 1)
        self.assertFalse(self.mix.id_existing)
        self.assertFalse(self.mix.name_existing)
        # self.mix.name is kept for user help output
        self.assertFalse(self.mix.venue)
        self.assertFalse(self.mix.played)
        print("TestMix.delete: DONE\n")

    def test_get_one_mix_track(self):
        print("\nTestMix.get_one_mix_track: BEGIN")
        self.mix = Mix(False, 125, self.db_path)
        db_return = self.mix.get_one_mix_track(2) # get track #2
        #print(db_return.keys())
        #for col in db_return:
        #    log.debug(col)
        self.assertEqual(len(db_return), 12) # select returns 12 cols
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
        print("TestMix.get_one_mix_track: DONE\n")

    def test_get_tracks_of_one_mix(self):
        print("\nTestMix.get_tracks_of_one_mix: BEGIN")
        self.mix = Mix(False, 125, self.db_path)
        db_return = self.mix.get_tracks_of_one_mix()
        self.assertEqual(len(db_return), 2)
        self.assertEqual(db_return[0]["mix_id"], 125)
        self.assertEqual(db_return[0]["d_release_id"], 123456)
        self.assertEqual(db_return[0]["d_track_no"], "A1")
        self.assertEqual(db_return[1]["mix_id"], 125)
        self.assertEqual(db_return[1]["d_release_id"], 123456)
        self.assertEqual(db_return[1]["d_track_no"], "B2")
        print("TestMix.get_tracks_of_one_mix: DONE\n")

    def test_get_all_tracks_in_mixes(self):
        print("\nTestMix.get_all_tracks_in_mixes: BEGIN")
        self.mix = Mix(False, 0, self.db_path)
        db_return = self.mix.get_all_tracks_in_mixes()
        #self.assertEqual(len(db_return), 4) # this will vary if we add tracks, screw it
        self.assertEqual(db_return[0]["mix_id"], 125)
        self.assertEqual(db_return[0]["d_release_id"], 123456)
        self.assertEqual(db_return[0]["d_track_no"], "A1")
        self.assertEqual(db_return[3]["mix_id"], 126)
        self.assertEqual(db_return[3]["d_release_id"], 123456)
        self.assertEqual(db_return[3]["d_track_no"], "B2")
        print("TestMix.get_all_tracks_in_mixes: DONE\n")

    def test_get_mix_info(self):
        print("\nTestMix.get_mix_info: BEGIN")
        self.mix = Mix(False, 126, self.db_path)
        db_return = self.mix.get_mix_info()
        self.assertEqual(len(db_return), 6)
        self.assertTrue(self.mix.id_existing)
        self.assertTrue(self.mix.name_existing)
        self.assertEqual(self.mix.name, "test mix 126")
        self.assertEqual(self.mix.venue, "test venue")
        self.assertEqual(self.mix.played, "2020-01-01")
        print("TestMix.get_mix_info: DONE\n")

    def test_get_last_track(self):
        print("\nTestMix.get_last_track: BEGIN")
        self.mix = Mix(False, 125, self.db_path)
        db_return = self.mix.get_last_track()
        self.assertEqual(len(db_return), 1)
        #self.assertEqual(db_return["track_pos"], 2) # no named cols in this case?
        self.assertEqual(db_return[0], 2) # maybe we use like this somewhere
        print("TestMix.get_last_track: DONE\n")

    def test_add_track(self):
        print("\nTestMix.add_track: BEGIN")
        self.mix = Mix(False, 127, self.db_path)
        db_ret_add = self.mix.add_track("123456", "B2", 5, 'üüü', '@@@')
        self.assertEqual(db_ret_add, 1)
        db_return = self.mix.get_one_mix_track(5) # get track #2
        self.assertEqual(len(db_return), 12) # select returns 12 cols
        self.assertEqual(db_return["track_pos"], 5)
        self.assertEqual(db_return["discogs_title"], "Material Love")
        self.assertEqual(db_return["d_track_name"], "Hedup!")
        self.assertEqual(db_return["d_track_no"], "B2")
        self.assertEqual(db_return["trans_rating"], "üüü")
        self.assertEqual(db_return["trans_notes"], "@@@")
        self.assertEqual(db_return["key"], "C")
        self.assertEqual(db_return["bpm"], 130)
        print("TestMix.add_track: DONE\n")

    def test_delete_track(self):
        print("\nTestMix.delete_track: BEGIN")
        self.mix = Mix(False, 128, self.db_path)
        db_ret_add = self.mix.delete_track(3)
        self.assertEqual(db_ret_add, 1)
        db_return = self.mix.get_one_mix_track(3) # get the track we just deleted
        self.assertEqual(len(db_return), 0) # select should return nothing
        print("TestMix.delete_track: DONE\n")

    def test_reorder_tracks(self):
        print("\nTestMix.reorder_tracks: BEGIN")
        self.mix = Mix(False, 129, self.db_path) # mix 129 is missing track_pos 5
        db_ret_reord = self.mix.reorder_tracks(4) # reorder starts at pos 4
        self.assertEqual(db_ret_reord, 1)
        db_get_ret = self.mix.get_one_mix_track(5) # get the track_pos that was the gap
        self.assertEqual(len(db_get_ret), 12) # select should return 12 columns
        self.assertEqual(db_get_ret['d_track_name'],
            'Material Love (Cab Drivers Remix)') # pos 5 should be this track now
        print("TestMix.reorder_tracks: DONE\n")

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

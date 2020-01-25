import unittest
from shutil import copy2
from os import remove
from discodos.models import *
from discodos.utils import *


class TestMix(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        log.handlers[0].setLevel("INFO") # handler 0 is the console handler
        log.handlers[0].setLevel("DEBUG") # handler 0 is the console handler
        conf = Config() # doesn't get path of test-db, so...
        empty_db_path = conf.discodos_root / 'tests' / 'fixtures' / 'discobase_empty.db'
        self.db_path = conf.discodos_root / 'tests' / 'discobase.db'
        print('TestMix.setUpClass: test-db: {}'.format(copy2(empty_db_path, self.db_path)))
        print("TestMix.setUpClass: done\n")

    def test_mix_non_existent(self):
        print("\nTestMix.mix_non_existent: BEGIN")
        # instantiate the Mix model class (empty, mix 123 = non-existent)
        self.mix = Mix(False, 123, self.db_path) 
        self.assertFalse(self.mix.id_existing)
        print("TestMix.mix_non_existent: DONE\n")

    def test_mix_create(self):
        print("\nTestMix.mix_create: BEGIN")
        self.mix = Mix(False, 123, self.db_path) 
        db_return = self.mix.create("2020-01-01", "test venue", "test mix 1")
        self.assertEqual(db_return, 1)
        self.assertTrue(self.mix.id_existing)
        self.assertTrue(self.mix.name_existing)
        self.assertEqual(self.mix.name, "test mix 1")
        self.assertEqual(self.mix.venue, "test venue")
        self.assertEqual(self.mix.played, "2020-01-01")
        print("TestMix.mix_create: DONE\n")

    def test_mix_delete(self):
        print("\nTestMix.mix_delete: BEGIN")
        self.mix = Mix(False, 124, self.db_path)
        db_return = self.mix.delete()
        self.assertEqual(db_return, 1)
        self.assertFalse(self.mix.id_existing)
        self.assertFalse(self.mix.name_existing)
        self.assertFalse(self.mix.name)
        self.assertFalse(self.mix.venue)
        self.assertFalse(self.mix.played)
        print("TestMix.mix_delete: DONE\n")

    @classmethod
    def tearDownClass(self):
        os.remove(self.db_path)
        print("\nTestMix.teardownClass: done")

if __name__ == '__main__':
    unittest.main()

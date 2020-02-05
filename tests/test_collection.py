#!/usr/bin/env python
import unittest
from shutil import copy2
from os import remove
from discodos.models import *
from discodos.utils import *


class TestCollection(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        log.handlers[0].setLevel("INFO") # handler 0 is the console handler
        log.handlers[0].setLevel("DEBUG") # handler 0 is the console handler
        conf = Config() # doesn't get path of test-db, so...
        empty_db_path = conf.discodos_root / 'tests' / 'fixtures' / 'discobase_empty.db'
        self.db_path = conf.discodos_root / 'tests' / 'discobase.db'
        print('TestMix.setUpClass: test-db: {}'.format(copy2(empty_db_path, self.db_path)))
        print("TestMix.setUpClass: done\n")

    def test_get_all_db_releases(self):
        print("\nTestMix.get_all_db_releases: BEGIN")
        # instantiate the Collection model class
        self.collection = Collection(False, self.db_path) 
        db_return = self.collection.get_all_db_releases()
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 2)
        self.assertEqual(db_return[0]['discogs_id'], 123456)
        self.assertEqual(db_return[0]['discogs_title'], 'Material Love')
        #self.assertEqual(db_return[0]['import_timestamp'], '2020-01-25 22:33:35')
        self.assertEqual(db_return[0]['d_artist'], 'Märtini Brös.')
        #self.assertEqual(db_return[0]['in_d_collection'], 1)
        self.assertEqual(db_return[1]['discogs_id'], 8620643)
        self.assertEqual(db_return[1]['discogs_title'], 'The Crane')
        #self.assertEqual(db_return[1]['import_timestamp'], '2020-01-30 10:06:26')
        self.assertEqual(db_return[1]['d_artist'], 'Source Direct')
        #self.assertEqual(db_return[1]['in_d_collection'], 1)
        print("TestMix.get_all_db_releases: DONE\n")

    def test_search_release_id(self):
        print("\nTestMix.search_release_id: BEGIN")
        # instantiate the Collection model class
        self.collection = Collection(False, self.db_path)
        db_return = self.collection.search_release_id('123456')
        self.assertIsNotNone(db_return)
        self.assertEqual(len(db_return), 5) # should be 5 columns
        self.assertEqual(db_return['discogs_id'], 123456)
        self.assertEqual(db_return['d_artist'], 'Märtini Brös.')
        self.assertEqual(db_return['discogs_title'], 'Material Love')
        print("TestMix.search_release_id: DONE\n")

    @classmethod
    def tearDownClass(self):
        os.remove(self.db_path)
        print("\nTestMix.teardownClass: done")

if __name__ == '__main__':
    loader = unittest.TestLoader()
    ln = lambda f: getattr(TestCollection, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    loader.sortTestMethodsUsing = lncmp
    unittest.main(testLoader=loader, verbosity=2)

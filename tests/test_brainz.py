from pprint import pprint
import inspect
import os
import unittest
from pathlib import Path
from shutil import copy2

from discodos.config import Config
from discodos.model import Brainz, Brainz_match


class TestBrainz(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        #log.handlers[0].setLevel("INFO") # handler 0 is the console handler
        #log.handlers[0].setLevel("DEBUG")
        self.conf = Config() # doesn't get path of test-db, so...
        discodos_tests = Path(os.path.dirname(os.path.abspath(__file__)))
        empty_db_path = discodos_tests / 'fixtures' / 'discobase_empty.db'
        self.db_path = discodos_tests / 'discobase.db'
        self.clname = self.__name__ # just handy a shortcut, used in test output
        self.mb_user = self.conf.musicbrainz_user
        self.mb_pass = self.conf.musicbrainz_password
        self.mb_appid = self.conf.musicbrainz_appid
        print('TestBrainz.setUpClass: test-db: {}'.format(copy2(empty_db_path, self.db_path)))
        print("TestBrainz.setUpClass: done\n")

    def test_get_mb_artist_by_id(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.brainz = Brainz(self.mb_user,self.mb_pass,self.mb_appid)
        if self.brainz.ONLINE:
            print('We are ONLINE')
            mb_return = self.brainz.get_mb_artist_by_id('952a4205-023d-4235-897c-6fdb6f58dfaa')
            #print(dir(mb_return))
            #print(mb_return)
            self.assertEqual(len(mb_return), 1) # should be single release in a list!
            self.assertEqual(mb_return['artist']['name'], 'Dynamo Go')
            self.assertEqual(mb_return['artist']['country'], 'NZ')
        else:
            print('We are OFFLINE, testing if we properly fail!')
            mb_return = self.brainz.get_mb_artist_by_id('952a4205-023d-4235-897c-6fdb6f58dfaa')
            self.assertFalse(mb_return)
        print("{} - {} - END".format(self.clname, name))

    def test_search_mb_releases(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.brainz = Brainz(self.mb_user,self.mb_pass,self.mb_appid)
        if self.brainz.ONLINE:
            print('We are ONLINE')
            mb_return = self.brainz.search_mb_releases("Source Direct",
                "The Crane", "NONPLUS034")
            #print(dir(mb_return))
            #print(mb_return)
            #pprint(mb_return)
            self.assertEqual(len(mb_return), 2) # keys: release-list, release-count
            self.assertEqual(
                mb_return['release-list'][0]['artist-credit'][0]['artist']['name'],
                'Source Direct')
            self.assertEqual(
                mb_return['release-list'][0]['label-info-list'][0]['catalog-number'],
                'NONPLUS034')
            # we don't get url-rels with a release search
        else:
            print('We are OFFLINE, testing if we properly fail!')
            mb_return = self.brainz.search_mb_releases("Source Direct",
                "The Crane")
            self.assertFalse(mb_return)
        print("{} - {} - END".format(self.clname, name))

    def test_get_mb_release_by_id(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.brainz = Brainz(self.mb_user,self.mb_pass,self.mb_appid)
        if self.brainz.ONLINE:
            print('We are ONLINE')
            mb_return = self.brainz.get_mb_release_by_id(
                'c4b619f1-5ae2-45e5-b848-71290e97eb69')
            #print(dir(mb_return))
            #pprint(mb_return)
            #print(mb_return.items())
            self.assertEqual(len(mb_return), 1) # should be single release in a list!
            self.assertEqual(
                mb_return['release']['artist-credit'][0]['artist']['name'],
                'Source Direct')
            self.assertEqual(
                mb_return['release']['label-info-list'][0]['catalog-number'],
                'NONPLUS034')
            self.assertEqual(
                mb_return['release']['url-relation-list'][0]['type'], 'discogs')
            self.assertEqual(
                mb_return['release']['url-relation-list'][0]['type-id'],
                '4a78823c-1c53-4176-a5f3-58026c76f2bc')
            self.assertEqual(
                mb_return['release']['url-relation-list'][0]['target'],
                'https://www.discogs.com/release/8633263')
        else:
            print('We are OFFLINE, testing if we properly fail!')
            mb_return = self.brainz.get_mb_release_by_id(
                'c4b619f1-5ae2-45e5-b848-71290e97eb69')
            self.assertFalse(mb_return)
        print("{} - {} - END".format(self.clname, name))

    def test_get_mb_recording_by_id(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.brainz = Brainz(self.mb_user,self.mb_pass,self.mb_appid)
        if self.brainz.ONLINE:
            print('We are ONLINE')
            mb_return = self.brainz.get_mb_recording_by_id(
                'fa9b7b2d-e9bb-4122-a725-4f865dd4648a')
            self.assertEqual(len(mb_return), 1) # should be single release in a list!
            self.assertEqual(mb_return['recording']['id'],
                'fa9b7b2d-e9bb-4122-a725-4f865dd4648a')
            self.assertEqual(mb_return['recording']['title'], 'The Crane')
        else:
            print('We are OFFLINE, testing if we properly fail!')
            mb_return = self.brainz.get_mb_recording_by_id(
                'fa9b7b2d-e9bb-4122-a725-4f865dd4648a')
            self.assertFalse(mb_return)
        print("{} - {} - END".format(self.clname, name))

    def test_get_accbr_low_level(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.brainz = Brainz(self.mb_user,self.mb_pass,self.mb_appid)
        if self.brainz.ONLINE:
            print('We are ONLINE')
            ab_return = self.brainz._get_accbr_low_level(
                'fa9b7b2d-e9bb-4122-a725-4f865dd4648a')
            #pprint(ab_return)
            self.assertEqual(ab_return['rhythm']['beats_count'], 836)
            self.assertEqual(int(ab_return['rhythm']['bpm']), 108)
            self.assertEqual(ab_return['rhythm']['danceability'], 1.06401479244)
            self.assertEqual(ab_return['tonal']['chords_key'], 'A#')
            self.assertEqual(ab_return['tonal']['chords_scale'], 'minor')
            self.assertEqual(ab_return['tonal']['key_key'], 'A#')
            self.assertEqual(ab_return['tonal']['key_scale'], 'minor')

        else:
            print('We are OFFLINE, testing if we properly fail!')
            ab_return = self.brainz._get_accbr_low_level(
                'fa9b7b2d-e9bb-4122-a725-4f865dd4648a')
            self.assertFalse(ab_return)
        print("{} - {} - END".format(self.clname, name))

    def test_get_accbr_high_level(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        self.brainz = Brainz(self.mb_user,self.mb_pass,self.mb_appid)
        if self.brainz.ONLINE:
            print('We are ONLINE')
            ab_return = self.brainz._get_accbr_high_level(
                'fa9b7b2d-e9bb-4122-a725-4f865dd4648a')
            #pprint(ab_return)
            self.assertEqual(
                ab_return['highlevel']['danceability']['all']['danceable'],
                0.999491930008)
            self.assertEqual(
                ab_return['highlevel']['danceability']['all']['not_danceable'],
                0.000508077442646)
            self.assertEqual(
                ab_return['highlevel']['danceability']['probability'],
                0.999491930008)
        else:
            print('We are OFFLINE, testing if we properly fail!')
            ab_return = self.brainz._get_accbr_high_level(
                'fa9b7b2d-e9bb-4122-a725-4f865dd4648a')
            self.assertFalse(ab_return)
        print("{} - {} - END".format(self.clname, name))

    def test_catno_match_cutter_var_2(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        print(self.mb_appid)
        bmatch = Brainz_match(self.mb_user, self.mb_pass, self.mb_appid, 
              6762725, 'Imperial Propaganda', 'MONNOM BLACK 005',
              'Dax J', 'Imperial Propaganda', 'A1', 1)
        # no auto-ws-stripping here, in reality done after fetch mb_releases
        cutter_return = bmatch._catno_cutter('MONNOMBLACK005', 'BLACK')
        self.assertEqual(cutter_return['before'], 'MONNOM')
        self.assertEqual(cutter_return['term'], 'BLACK')
        self.assertEqual(cutter_return['after'], '005')
        print("{} - {} - END".format(self.clname, name))

    @classmethod
    def tearDownClass(self):
        os.remove(self.db_path)
        print("\nTestBrainz.teardownClass: done")

if __name__ == '__main__':
    loader = unittest.TestLoader()
    ln = lambda f: getattr(TestCollection, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    loader.sortTestMethodsUsing = lncmp
    unittest.main(testLoader=loader, verbosity=2)
#!/usr/bin/env python
import inspect
import unittest
from sqlite3 import Row
from unittest.mock import patch
from pathlib import Path
import os

from discodos.config import Config, create_data_dir  # , Db_setup
from discodos.models import log


class TestConfig(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        name = inspect.currentframe().f_code.co_name
        self.clname = self.__name__  # just handy a shortcut, used in test output
        print("\n{} - {} - BEGIN".format(self.clname, name))
        #log.handlers[0].setLevel("INFO")  # handler 0 is the console handler
        #log.handlers[0].setLevel("DEBUG")  # handler 0 is the console handler
        self.tests_path = Path(os.path.dirname(os.path.abspath(__file__)))
        self.discodos_data = create_data_dir(self.tests_path)
        self.config_file = self.discodos_data / 'config.yaml'
        print("{} - {} - END\n".format(self.clname, name))

    @patch('builtins.input', return_value='token123')
    def test_config(self, input):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        log.info(f'This is self.tests_path: {self.tests_path}')
        log.info(f'This is self.discodos_data: {self.discodos_data}')
        log.info(f'This is self.config_file: {self.config_file}')
        conf_exists = self.config_file.exists()
        log.info(f'Config file exists: {conf_exists}')

        # different test depending on file exists or not
        if conf_exists:
            conf = Config()  # wants user input
            self.assertEqual(conf.discogs_token, 'token123')
        else:
            # first ever config init prints info, creates config.yaml
            # and raises SystemExit(0)
            with self.assertRaises(SystemExit) as cm:
                Config()
                self.assertEqual(cm.exception.code, 0)
        print("{} - {} - END\n".format(self.clname, name))

    def debug_db(self, db_return):
        #print(db_return.keys())
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
            print('unknown datatype, cannot debug')
        return True


    @classmethod
    def tearDownClass(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        #os.remove(self.db_path)
        print("{} - {} - END\n".format(self.clname, name))


if __name__ == '__main__':
    loader = unittest.TestLoader()
    ln = lambda f: getattr(TestConfig, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    loader.sortTestMethodsUsing = lncmp
    unittest.main(testLoader=loader, verbosity=2)

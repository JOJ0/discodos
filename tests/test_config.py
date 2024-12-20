from cgi import print_environ
import inspect
import unittest
from sqlite3 import Row
from unittest.mock import patch
from pathlib import Path
import os

from discodos.config import Config, create_data_dir  # , Db_setup


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

    @patch('builtins.input', return_value='token123')  # Patch user prompt.
    def test_config(self, input):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        print(f'self.tests_path is {self.tests_path}')
        print(f'self.discodos_data is {self.discodos_data}')
        # Depending on whether or not a config file was found we have to check
        # for different behaviour.
        if not self.config_file.exists():
            print(f'This is a first-run, no config file found.')
            # First ever Config initialization prints info, creates config.yaml
            # and raises SystemExit(0)
            with self.assertRaises(SystemExit) as cm:
                Config()
                self.assertEqual(cm.exception.code, 0)
        else:
            print(f'Existing config file found: {self.config_file}')
            conf = Config()  # Wants user input if discogs_token missing.
            if os.environ.get('GITHUB_ACTIONS') == 'true':
                # Check for dummy token when running from gh-actions.
                self.assertEqual(conf.discogs_token, 'token123')
            else:
                print('Skipping discogs_token check, not a gh-actions run.')
        print("{} - {} - END\n".format(self.clname, name))

    @classmethod
    def tearDownClass(self):
        name = inspect.currentframe().f_code.co_name
        print("\n{} - {} - BEGIN".format(self.clname, name))
        print("{} - {} - END\n".format(self.clname, name))


if __name__ == '__main__':
    loader = unittest.TestLoader()
    ln = lambda f: getattr(TestConfig, f).im_func.func_code.co_firstlineno
    lncmp = lambda _, a, b: cmp(ln(a), ln(b))
    loader.sortTestMethodsUsing = lncmp
    unittest.main(testLoader=loader, verbosity=2)

#!/usr/bin/env python

# config.py is kind of a controller - it sets up db and creates config
from discodos.models import Database, sqlerr
from discodos.views import User_int
from discodos.utils import read_yaml, print_help, ask_user
import yaml
import logging
import pprint
from pathlib import Path
import os
import sys
import platform
from subprocess import run
from shutil import copy2

log = logging.getLogger('discodos')

def create_data_dir(discodos_root):
    # create discodos_data dir
    if platform.system() == "Darwin" and getattr(sys, 'frozen', False):
        # only in mac-app installs we want Documents/DiscoDOS dir
        home = Path(os.getenv('HOME'))
        Path.mkdir(home / 'Documents' / 'DiscoDOS', exist_ok=True)
        discodos_data = home / 'Documents' / 'DiscoDOS'
    elif os.name == 'nt':
        #import win32com.client
        #from win32 import win32api
        #oShell = win32com.client.Dispatch("Wscript.Shell")
        #mydocs = oShell.SpecialFolders("MyDocuments")
        #discodos_data = mydocs / 'discodos'
        import ctypes.wintypes
        CSIDL_PERSONAL=5
        SHGFP_TYPE_CURRENT= 0
        buf= ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf)
        mydocs = Path(buf.value)
        Path.mkdir(mydocs / 'DiscoDOS/', exist_ok=True)
        discodos_data = mydocs / 'DiscoDOS'
    elif os.name == 'posix':
        home = Path(os.getenv('HOME'))
        Path.mkdir(home / '.discodos/', exist_ok=True)
        discodos_data = home / '.discodos'
    else:
        log.warn("Config: Unknown OS - using discodos_root as data dir too.")
        discodos_data = discodos_root
    return discodos_data


class Db_setup(Database):
    def __init__(self, _db_file):
        super().__init__(db_file = _db_file, setup = True)
        self.sql_initial = {
            'release':
            """ CREATE TABLE release (
                  discogs_id INTEGER PRIMARY KEY ON CONFLICT REPLACE,
                  discogs_title TEXT NOT NULL,
                  import_timestamp TEXT,
                  d_artist TEXT,
                  in_d_collection INTEGER
                  ); """,
            'mix':
            """ CREATE TABLE mix (
                  mix_id INTEGER PRIMARY KEY,
                  name TEXT,
                  created TEXT,
                  updated TEXT,
                  played TEXT,
                  venue TEXT
                  ); """,
            'mix_track':
            """ CREATE TABLE mix_track (
                  mix_track_id INTEGER PRIMARY KEY,
                  mix_id INTEGER,
                  d_release_id INTEGER NOT NULL,
                  d_track_no TEXT NOT NULL,
                  track_pos INTEGER NOT NULL,
                  trans_rating TEXT,
                  trans_notes TEXT,
                  FOREIGN KEY (mix_id)
                     REFERENCES mix(mix_id)
                  ON DELETE CASCADE
                  ON UPDATE CASCADE
                  ); """,
            'track':
            """ CREATE TABLE track (
                  d_release_id INTEGER NOT NULL,
                  d_track_no TEXT NOT NULL,
                  d_artist TEXT,
                  d_track_name TEXT,
                  import_timestamp TEXT,
                  PRIMARY KEY (d_release_id, d_track_no)
                  ); """,
                  # We had this constraints once...
                  # FOREIGN KEY (d_release_id)
                  #     REFERENCES release(d_discogs_id)
            # the initial idea of track_ext was to "extend" discogs data with some fields
            'track_ext':
            """ CREATE TABLE track_ext (
                  d_release_id INTEGER NOT NULL,
                  d_track_no TEXT NOT NULL,
                  key TEXT,
                  key_notes TEXT,
                  bpm REAL,
                  notes TEXT,
                  PRIMARY KEY (d_release_id, d_track_no)
                  ); """}

        self.sql_upgrades = [    # list element 0 contains a dict
           {'schema_version': 2, # this dict contains 2 entries: schema and tasks
            'tasks': {           # tasks entry contains another dict with a lot of entries
                'Add field track.m_rec_id': 'ALTER TABLE track ADD m_rec_id TEXT;',
                'Add field track.m_match_method': 'ALTER TABLE track ADD m_match_method TEXT;',
                'Add field track.m_match_time': 'ALTER TABLE track ADD m_match_time TEXT;',
                'Add field track.a_key': 'ALTER TABLE track ADD a_key TEXT;',
                'Add field track.a_chords_key': 'ALTER TABLE track ADD a_chords_key TEXT;',
                'Add field track.a_bpm': 'ALTER TABLE track ADD a_bpm REAL;',
                'Add field track_ext.m_rec_id_override': 'ALTER TABLE track_ext ADD m_rec_id_override TEXT;',
                'Add field release.m_rel_id': 'ALTER TABLE release ADD m_rel_id TEXT;',
                'Add field release.m_rel_id_override': 'ALTER TABLE release ADD m_rel_id_override TEXT;',
                'Add field release.m_match_method': 'ALTER TABLE release ADD m_match_method TEXT;',
                'Add field release.m_match_time': 'ALTER TABLE release ADD m_match_time TEXT;',
                'Add field release.d_catno': 'ALTER TABLE release ADD d_catno TEXT;'
             }
           }                       # list element 0 ends here
           #{'schema_version': 3,  # list element 1 starts here
           # 'tasks': {
           #     'Add field track.test_upgrade': 'ALTER TABLE track ADD test_upgrade TEXT;',
           # }
           #}                      # list element 1 ends here
        ]                          # list closes here

    def create_tables(self): # initial db setup
        for table, sql in self.sql_initial.items():
            try: # release
                self.execute_sql(sql, raise_err = True)
                msg_release="CREATE TABLE '{}' was successful.".format(table)
                log.info(msg_release)
                print(msg_release)
            except sqlerr as e:
                log.info("CREATE TABLE '%s': %s", table, e.args[0])

    def get_latest_schema_version(self):
        vers_list = [schema['schema_version'] for schema in self.sql_upgrades]
        latest = max(vers_list)
        log.debug('Db_setup: Latest DiscoBASE schema version: {}'.format(latest))
        return latest

    def get_current_schema_version(self):
        curr_vers_row = self._select('PRAGMA user_version', fetchone = True)
        return int(curr_vers_row['user_version'])

    def upgrade_schema(self, force_upgrade = False):
        current_schema = self.get_current_schema_version()
        latest_schema = self.get_latest_schema_version()
        # check if upgrade necessary
        if not current_schema < latest_schema and force_upgrade == False:
            log.info('Db_setup: No schema upgrade necessary.')
        else: # also happens if force_upgrade True
            print("Upgrading DiscoBASE schema to latest version.")
            failure = False
            self.execute_sql('PRAGMA foreign_keys = OFF;')
            for upgrade in self.sql_upgrades: # list is sorted -> execute all up to highest
                current_schema = self.get_current_schema_version()
                if (current_schema < upgrade['schema_version'] or force_upgrade == True):
                    for task, sql in upgrade['tasks'].items():
                        try:
                            self.execute_sql(sql, raise_err = True)
                            msg_task="Task '{}' was successful.".format(task)
                            log.info(msg_task)
                            print(msg_task)
                        except sqlerr as e:
                            log.warning("Task failed '%s': %s", task, e.args[0])
                            failure = True

            if failure:
                msg_fail='DiscoBASE schema upgrade failed, open an issue on Github!\n'
                log.info(msg_fail)
                print(msg_fail)
                self.configure_db() # this sets foreign_keys = ON again
                return False
            else:
                self.execute_sql('PRAGMA user_version = {}'.format(latest_schema))
                msg_done='DiscoBASE schema upgrade done!\n'
                log.info(msg_done)
                print(msg_done)
                self.configure_db() # this sets foreign_keys = ON again
                return True


class Config():
    def __init__(self, no_create_conf=False):
        # is set to true on initial run and config create
        self.config_created = False
        self.no_create_conf = no_create_conf
        # path handling
        # determine if application is a script file or frozen exe
        if getattr(sys, 'frozen', False):
            self.frozen = True
            log.debug("Config.frozen: Running as a bundled executable.")
            self.discodos_root = Path(os.path.dirname(sys.executable))
            self.discodos_data = create_data_dir(self.discodos_root)
        else:
            log.debug("Config.frozen: Running as a Python script.")
            self.frozen = False
            # where is our library? how are we running?
            discodos_lib = Path(os.path.dirname(os.path.abspath(__file__)))
            log.info('Config: discodos package is in: {}'.format(discodos_lib))
            # discodos_root is where our wrappers should be placed in
            # but we only want them when running frozen
            self.discodos_root = discodos_lib
            self.venv = os.getenv('VIRTUAL_ENV')
            # in unfrozen we need to find proper place for data_dir
            self.discodos_data = create_data_dir(self.discodos_root)
            # currently no difference if in venv or not - leave this for now
            if self.venv == None:
                log.info('Config: We are _not_ in a venv.')
            else:
                log.info('Config: We are running in a venv: {}'.format(self.venv))
        log.info("Config.discodos_root: {}".format(self.discodos_root))
        log.info("Config.discodos_data: {}".format(self.discodos_data))

        # config.yaml path
        self.file = self.discodos_data / "config.yaml"

        # try to get a configuration from config file
        self.conf = read_yaml(self.file)
        if not self.conf:
            # on windows when user clicks Startmenu "Edit Conf...",
            # we show a popup and ask for rerun
            if self.no_create_conf and os.name == "nt":
                log.info("Config: We are running Windows and no_create_conf is set. Not creating a config file!")
                import ctypes  # An included library with Python install.
                ctypes.windll.user32.MessageBoxW(0,
                  "No configuration file existing yet, please run DiscoDOS first!", "DiscoDOS", 0)
                raise SystemExit(0)
            # SystemExit on macOS is evil - We don't create a config, just log
            # this is invoked from open_shell_mac.py
            elif self.no_create_conf and platform.system() == "Darwin":
                log.info("Config: We are running macOS and no_create_conf is set. Not creating a config file!")
            # on a shell we just create config and show steps,
            else:
                self.create_conf()
                raise SystemExit(0)

        # The only setting we _always_ try to fetch is log_level!!!
        try: # optional setting log_level
            self.log_level = self.conf["log_level"]
            log.info("config.yaml entry log_level is {}.".format(
                self.log_level))
        except KeyError:
            self.log_level = "WARNING"
            log.warn("config.yaml entry log_level not set, taking log_level from CLI option or default (WARNING).")
        except: # any other error: set INFO
            self.log_level = "WARNING"
            log.warn("config.yaml not existing or other error, setting log_level to WARNING.")

        # Don't fetch settings when no_create_conf is set
        # (Config init from open_shell_mac.py)
        # Windows is existing above, this is only necessary for macOS because
        # SystemExit is evil in a mac app!
        if self.no_create_conf == False:
            # db file handling
            db_file = self._get_config_entry('discobase_file') # maybe configured?
            if not db_file: # if not set, use default value
                db_file = 'discobase.db'
            self.discobase = self.discodos_data / db_file
            log.info("Config.discobase: {}".format(self.discobase))

            # then other settings
            self.discogs_appid = 'DiscoDOS/1.0 +https://github.com/JOJ0/discodos'
            self.musicbrainz_appid = ['1.0', 'DiscoDOS https://github.com/JOJ0/discodos']
            self.dropbox_token = self._get_config_entry('dropbox_token')
            self.musicbrainz_user = self._get_config_entry('musicbrainz_user')
            self.musicbrainz_password = self._get_config_entry('musicbrainz_password')
            self.webdav_user = self._get_config_entry('webdav_user')
            self.webdav_password = self._get_config_entry('webdav_password')
            self.webdav_url = self._get_config_entry('webdav_url')

            # discogs_token is essential, bother user until we have one
            # but not when no_ask_token is set (macOS)
            self.discogs_token = self._get_config_entry('discogs_token', False)
            if self.discogs_token == '':
                token = ''
                while token == '':
                    token = ask_user("Please input discogs_token: ")
                self.conf['discogs_token'] = token
                written = self._write_yaml(self.conf, self.file)
                if written:
                    log.info('Config: config.yaml written successfully.')
                    self.discogs_token = self._get_config_entry('discogs_token', False)
                else:
                    log.error('writing config.yaml.')

    def _get_config_entry(self, yaml_key, optional = True):
        if optional:
            try:
                if self.conf[yaml_key] == '':
                    value = ''
                    log.info("config.yaml entry {} is empty.".format(yaml_key))
                else:
                    value = self.conf[yaml_key]
                    log.info("config.yaml entry {} is set.".format(yaml_key))
            except KeyError:
                value = ''
                log.info("config.yaml entry {} is missing.".format(yaml_key))
            return value
        else:
            try: # essential settings entries should error and exit
                value = self.conf[yaml_key]
            except KeyError as ke:
                log.error("Missing essential entry in config.yaml: {}".format(ke))
                raise SystemExit(3)
            return value

    # install cli command (disco) into discodos_root
    def install_cli(self, to_path=False):
        # when to_path is set, we install wrappers to ~/bin
        # and extend $PATH if necessary (posix only)
        log.info('Config.cli: We are on a "{}" OS'.format(os.name))
        # first part: compile info for wrappers together
        if os.name == 'posix':
            if self.frozen: # packaged
                venv_act = False
                disco_py = self.discodos_root / 'cli'
                sync_py = self.discodos_root / 'sync'
            else: # not packaged and in a venv (checked in config.py main())
                venv_act = Path(self.venv) / 'bin' / 'activate'
                disco_py = self.discodos_root / 'cmd' / 'cli.py'
                sync_py = self.discodos_root / 'cmd' / 'sync.py'

            # cli.py wrapper
            disco_wrapper = self.discodos_root / 'disco'
            disco_contents = self._posix_wrapper(disco_py, venv_act,
                  '# This is the DiscoDOS CLI wrapper.')

            # sync.py wrapper
            sync_wrapper = self.discodos_root / 'discosync'
            sync_contents = self._posix_wrapper(sync_py, venv_act,
                  '# This is the DiscoDOS sync/backup script wrapper.')

            # install systemwide
            sysinst_sh = self.discodos_root / 'install_wrappers_to_path.sh'
            sysinst_sh_contents = 'echo "Installing disco commands to your user environment..."\n'
            sysinst_sh_contents+= 'mkdir -v ~/bin\n'
            sysinst_sh_contents+= 'cp -v {} ~/bin\n'.format(disco_wrapper)
            sysinst_sh_contents+= 'cp -v {} ~/bin\n'.format(sync_wrapper)
            sysinst_sh_contents+= 'echo "Adding $HOME/bin to your PATH by appending a line to $HOME/.bashrc"\n'
            sysinst_sh_contents+= 'echo \'export PATH=~/bin:$PATH\' >> ~/.bashrc\n'
            sysinst_sh_contents+= 'read -p "Reload ~/.bashrc to activate changes? (y/N) " RELOAD\n'
            sysinst_sh_contents+= 'if [[ $RELOAD == "y" || $RELOAD == "Y" ]]; then\n'
            sysinst_sh_contents+= '    source ~/.bashrc\n'
            sysinst_sh_contents+= 'else\n'
            sysinst_sh_contents+= '    exit 0\n'
            sysinst_sh_contents+= 'fi\n'
        # first part: Windows wrappers
        elif os.name == 'nt':
            if self.frozen: # packaged
                venv_act = False
                disco_py = self.discodos_root / 'cli.exe'
                sync_py = self.discodos_root / 'sync.exe'
            else: # not packaged and in a venv (checked in config.py main())
                venv_act = Path(self.venv) / 'Scripts' / 'activate.bat'
                disco_py = self.discodos_root / 'cmd' / 'cli.py'
                sync_py = self.discodos_root / 'cmd' / 'sync.py'

            # WRAPPER cli.py - disco.bat
            disco_wrapper = self.discodos_root / 'disco.bat'
            disco_contents = self._win_wrapper(disco_py,
                  'rem This is the DiscoDOS CLI wrapper.', self.frozen)

            # WRAPPER sync.py - discosync.bat
            sync_wrapper = self.discodos_root / 'discosync.bat'
            sync_contents = self._win_wrapper(sync_py,
                  'rem This is the DiscoDOS sync/backup script wrapper.', self.frozen)

            # WRAPPER discoshell.bat
            discoshell = self.discodos_root / 'discoshell.bat'
            if venv_act:
                discoshell_contents = 'start "DiscoDOS shell" /D "{}" "{}"\n'.format(
                    self.discodos_root, venv_act)
            else:
                echo_hints = 'Launch disco.bat to view a usage tutorial'
                discoshell_contents = 'start "DiscoDOS shell" /D "{}" echo "{}"\n'.format(
                    self.discodos_root, echo_hints)
        # first part: else - unknown - no wrappers
        else:
            log.warn("Config.cli: Unknown OS - not creating CLI wrappers.")
            return True

        # second part: Posix file installation
        if os.name == "posix":
            log.info('Config.cli: Installing DiscoDOS wrappers.')

            # install cli wrapper
            if disco_wrapper.is_file(): # install only if non-existent
                log.info("Config.cli: CLI wrapper is already existing: {}".format(
                    disco_wrapper))
            else:
                print("Installing CLI wrapper: {}".format(disco_wrapper))
                self._write_textfile(disco_contents, disco_wrapper)
                disco_wrapper.chmod(0o755)
                print("You can now use the DiscoDOS CLI using ./disco\n")

            # install sync wrapper
            if sync_wrapper.is_file(): # install only if non-existent
                log.info("Config.cli: sync wrapper is already existing: {}".format(
                    sync_wrapper))
            else:
                print("Installing sync wrapper: {}".format(sync_wrapper))
                self._write_textfile(sync_contents, sync_wrapper)
                sync_wrapper.chmod(0o755)
                print("You can now use DiscoDOS sync using ./discosync\n")

            # install wrappers to path script
            if sysinst_sh.is_file(): # install only if non-existent
                log.info("Config.cli: install_wrappers_to_path.sh is already existing: {}".format(
                    sysinst_sh))
            else:
                self._write_textfile(sysinst_sh_contents, sysinst_sh)
                sysinst_sh.chmod(0o755)
                hlpmsg ="Execute ./{} to set up disco commands for your user environment!".format(
                    sysinst_sh.name)
                hlpmsg+="\n* makes disco command executable from everywhere. After installation you'd just type:"
                hlpmsg+="\ndisco"
                hlpmsg+="\ndiscosync"
                print_help(hlpmsg)

            if to_path == True:
                # handle path stuff
                home = Path(os.getenv('HOME'))
                Path.mkdir(home / 'bin', exist_ok=True)
                path = os.getenv('PATH')
                paths = path.split(os.pathsep)
                m_pth = 'Config: install to_path: $PATH currently is: {}'.format(paths)
                log.info(m_pth); print(m_pth)
                home_bin = home / 'bin'
                if str(home_bin) in paths:
                    m_alr ='Config: install to_path: $HOME/bin is already in PATH.'
                    log.info(m_alr); print(m_alr)
                else:
                    m_add = 'Config: install_to_path: Adding $HOME/bin to PATH.'
                    log.info(m_add); print(m_add)
                    bashrc_append_str = 'export PATH=~/bin:$PATH'
                    bashrc_append_cmd = 'echo \'{}\' >> {}/.bashrc'.format(bashrc_append_str, home)
                    m_bsh = 'Config: install_to_path: bashrc_append_cmd: {}'.format(bashrc_append_cmd)
                    log.info(m_bsh); print(m_bsh)
                    bashrc_success = run(bashrc_append_cmd, shell=True)
                    log.info('Config: bashrc_success: {}'.format(bashrc_success))
                    # this is only necessary for debugging mac packaging/installation
                    run('. {}/.bashrc'.format(home), shell=True)
                disco_wrapper_in_bin = home_bin / 'disco'
                sync_wrapper_in_bin = home_bin / 'discosync'
                # copy wrappers
                try:
                    if disco_wrapper_in_bin.is_file():
                        m_de = 'Config: disco wrapper already existing in ~/bin/'
                        log.info(m_de); print(m_de)
                    else:
                        m_cpd = 'Config: install_to_path: Copying disco wrapper to $HOME/bin.'
                        log.info(m_cpd); print(m_cpd)
                        copy2(disco_wrapper, home_bin)
                    if sync_wrapper_in_bin.is_file():
                        m_se = 'Config: discosync wrapper already existing in ~/bin/'
                        log.info(m_se); print(m_se)
                    else:
                        m_cps = 'Config: install_to_path: Copying discosync wrapper to $HOME/bin.'
                        log.info(m_cps); print(m_cps)
                        copy2(sync_wrapper, home_bin)
                except Exception as exc:
                    #tb = sys.exc_info()[3]
                    m_exc = 'Exception on copy: {}'.format(exc)
                    log.info(m_exc); print(m_exc)

        # second part: Windows file installation
        elif os.name == "nt":
            # INSTALL disco.bat
            if disco_wrapper.is_file(): # install only if non-existent
                log.info("Config.cli: CLI wrapper is already existing: {}".format(
                    disco_wrapper))
            else:
                msg_discoinst = ("Installing DiscoDOS CLI wrapper: {}".format(
                      disco_wrapper))
                print(msg_discoinst)
                self._write_textfile(disco_contents, disco_wrapper)
                print("You can now use the DiscoDOS CLI using disco.bat\n")

            # INSTALL discosync.bat
            if sync_wrapper.is_file(): # install only if non-existent
                log.info("Config.cli: sync wrapper is already existing: {}".format(
                    sync_wrapper))
            else:
                msg_syncinst = ("Installing DiscoDOS sync wrapper: {}".format(
                      sync_wrapper))
                print(msg_syncinst)
                self._write_textfile(sync_contents, sync_wrapper)
                print("You can now use DiscoDOS sync using discosync.bat\n")

            # INSTALL discoshell.bat
            # FIXME if
            if discoshell.is_file(): # install only if non-existent
                log.info("Config.cli: discoshell.bat is already existing: {}".format(
                    discoshell))
            else:
                print_help('Installing DiscoDOS shell: {}'.format(discoshell))
                self._write_textfile(discoshell_contents, discoshell)
                hlpshmsg = 'Usage: '
                hlpshmsg = 'Double click discoshell.bat to open the "DiscoDOS shell," '
                hlpshmsg+= '\nThen put DiscoDOS commands in there.'
                hlpshmsg+= '\nTo view help for available commands:'
                hlpshmsg+= '\ndisco -h'
                hlpshmsg+= '\ndisco mix -h'
                hlpshmsg+= '\ndisco search -h'
                hlpshmsg+= '\ndisco suggest -h'
                hlpshmsg+= '\ndisco import -h'
                hlpshmsg+= '\ndiscosync -h\n'
                print_help(hlpshmsg)

    def _posix_wrapper(self, filename, venv_activate, comment):
        '''return some lines forming a basic posix venv (or not) wrapper'''
        contents = '#!/bin/bash\n'
        contents+= '{}\n'.format(comment)
        if venv_activate:
            contents+= 'source "{}"\n'.format(venv_activate)
        contents+= '"{}" "$@"\n'.format(filename)
        return contents

    def _win_wrapper(self, filename, comment, frozen):
        '''return some lines forming a basic windows batch wrapper'''
        contents = '@echo off\n'
        contents+= '{}\n'.format(comment)
        contents+= 'setlocal enableextensions\n'
        if frozen:
            contents+= '"{}" %*\n'.format(filename)
        else:
            contents+= 'python "{}" %*\n'.format(filename)
        contents+= 'endlocal\n'
        return contents

    # write a textile (eg. shell script)
    def _write_textfile(self, contents, file):
        """contents expects string, file expects path/file"""
        try:
            with open(file, "w") as f_file:
                f_file.write(contents)
                log.info("File %s successfully written", file)
            return True
        except IOError as errio:
            log.error("IOError: could not write file %s \n\n", file)
            raise errio
        except Exception as err:
            log.error(" trying to write %s \n\n", file)
            raise err
            #raise SystemExit(3)

    def create_conf(self):
        '''creates config.yaml'''
        config = {
            'discogs_token': '',
            'log_level': "WARNING",
            'dropbox_token': '',
            'musicbrainz_user': '',
            'musicbrainz_password': '',
            'webdav_user': '',
            'webdav_password': '',
            'webdav_url': '',
            'discobase_file': 'discobase.db'
        }
        create_msg = '\nSeems like you are running DiscoDOS for the first time, '
        create_msg+= 'a config file will be created...\n'
        log.info(create_msg)
        print(create_msg)
        written = self._write_yaml(config, self.file)
        if written:
            m = 'Now:\n'
            m+= '* Get a Discogs API access token as described here:\n'
            m+= '  https://github.com/JOJ0/discodos/blob/master/INSTALLATION.md#configure-discogs-api-access\n'
            m+= '* Run DiscoDOS again (type disco) and input the token, '
            m+= 'setup will be completed and connection to Discogs verified.\n'
            m+= '* Then learn how to import your collection and use DiscoDOS:\n'
            m+= '  https://github.com/JOJ0/discodos/blob/master/README.md#importing-your-discogs-collection\n'
            m+= '* Sidenote: You can always open {} using a '.format(self.file)
            m+= 'texteditor and set your token manually (discogs_token: \'xyz\').\n'
            self.config_created = True
            log.info(m)
            print_help(m)


    def _write_yaml(self, data, yamlfile):
        """data expects dict, yamlfile expects path/file"""
        try:
            with open(yamlfile, "w") as fyamlfile:
                yaml.dump(data, fyamlfile, default_flow_style=False,
                                 allow_unicode=True)
                return True
        except IOError as errio:
            log.error("IOError: could not write file %s \n\n", yamlfile)
            raise errio
        except Exception as err:
            log.error(" trying to write %s \n\n", yamlfile)
            raise err
            raise SystemExit(3)

from discodos import log
import time
import yaml
from pathlib import Path
import os

# util: checks for numbers
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    except TypeError:
        return False

# util: print a UI message
def print_help(message):
    print(''+str(message)+'\n')

# util: ask user for some string
def ask_user(text=""):
    return input(text)

# read yaml
def read_yaml(yamlfile):
    """expects path/file"""
    try:
        with open(str(yamlfile), "r") as fyamlfile:
            return yaml.load(fyamlfile, Loader=yaml.SafeLoader)
    except IOError as errio:
        log.error("Can't find %s.", yamlfile)
        #raise errio
        #raise SystemExit(3)
        return False
    except yaml.parser.ParserError as errparse:
        log.error("ParserError in %s.", yamlfile)
        #raise errparse
        raise SystemExit(3)
    except yaml.scanner.ScannerError as errscan:
        log.error("ScannerError in %s.", yamlfile)
        #raise errscan
        raise SystemExit(3)
    except Exception as err:
        log.error(" trying to load %s.", yamlfile)
        raise err
        #raise SystemExit(3)

def join_sep(iterator, seperator):
    it = map(str, iterator)
    seperator = str(seperator)
    string = next(it, '')
    for s in it:
        string += seperator + s
    return string

class Config():
    def __init__(self):
        # path handling
        discodos_lib = Path(os.path.dirname(os.path.abspath(__file__)))
        self.discodos_root = discodos_lib.parents[0]
        log.info("Config.discodos_root: {}".format(self.discodos_root))
        # config.yaml handling
        self.conf = read_yaml( self.discodos_root / "config.yaml")
        if not self.conf:
            self.create_conf()
            raise SystemExit()
        # db file handling
        db_file = self._get_config_entry('discobase_file') # maybe configured?
        if not db_file: # if not set default value
            db_file = 'discobase.db'
        self.discobase = self.discodos_root / db_file
        log.info("Config.discobase: {}".format(self.discobase))

        try: # optional setting log_level
            self.log_level = self.conf["log_level"]
            log.info("config.yaml entry log_level is {}.".format(
                self.log_level))
        except KeyError:
            self.log_level = "WARNING"
            log.warn("config.yaml entry log_level not set, will take from cli option or default.")
        # then other settings
        self.discogs_token = self._get_config_entry('discogs_token', False)
        self.discogs_appid = 'DiscoDOS/1.0 +https://github.com/JOJ0/discodos'
        self.musicbrainz_appid = ['1.0', 'DiscoDOS https://github.com/JOJ0/discodos']
        self.dropbox_token = self._get_config_entry('dropbox_token')
        self.musicbrainz_user = self._get_config_entry('musicbrainz_user')
        self.musicbrainz_password = self._get_config_entry('musicbrainz_password')
        self.webdav_user = self._get_config_entry('webdav_user')
        self.webdav_password = self._get_config_entry('webdav_password')
        self.webdav_url = self._get_config_entry('webdav_url')

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
    def install_cli(self):
        log.info('Config.cli: We are on a "{}" OS'.format(os.name))
        if os.name == 'posix':
            venv_act = Path(os.getenv('VIRTUAL_ENV')) / 'bin' / 'activate'
            # cli.py wrapper
            disco_wrapper = self.discodos_root / 'disco'
            disco_py = self.discodos_root / 'cli.py'
            disco_contents = self._posix_wrapper(disco_py, venv_act,
                  '# This is the DiscoDOS cli wrapper.')
            # setup.py wrapper
            setup_wrapper = self.discodos_root / 'setup'
            setup_py = self.discodos_root / 'setup.py'
            setup_contents = self._posix_wrapper(setup_py, venv_act,
                  '# This is the DiscoDOS setup script wrapper.')
            # sync.py wrapper
            sync_wrapper = self.discodos_root / 'sync'
            sync_py = self.discodos_root / 'sync.py'
            sync_contents = self._posix_wrapper(sync_py, venv_act,
                  '# This is the DiscoDOS sync/backup script wrapper.')
            # install systemwide
            sysinst_sh = self.discodos_root / 'install_systemwide.sh'
            sysinst_sh_contents = 'sudo -p "Need your users password to allow '
            sysinst_sh_contents+= 'systemwide installation of disco cli command: " '
            sysinst_sh_contents+=  'cp {} /usr/local/bin\n'.format(disco_wrapper)
        elif os.name == 'nt':
            disco_wrapper = self.discodos_root / 'disco.bat'
            disco_contents = '@echo off\n'
            disco_contents+= 'rem This is the DiscoDOS cli wrapper.\n'
            disco_contents+= 'setlocal enableextensions\n'
            disco_contents+= '"{}" %*\n'.format(self.discodos_root / 'cli.py')
            disco_contents+= 'endlocal\n'
            discoshell = self.discodos_root / 'discoshell.bat'
            venv_act = Path(os.getenv('VIRTUAL_ENV')) / 'Scripts' / 'activate.bat'
            discoshell_contents = 'start "DiscoDOS shell" /D "{}" "{}"\n'.format(
                self.discodos_root, venv_act)
        else:
            log.warn("Config.cli: Unknown OS - not creating disco CLI wrapper.")
            return True

        # file installation part starts here
        if os.name == "posix":
            log.info('Config.cli: Installing DiscoDOS wrappers.')
            # install cli wrapper
            if disco_wrapper.is_file(): # install only if non-existent
                log.info("Config.cli: CLI wrapper is already existing: {}".format(
                    disco_wrapper))
            else:
                print("Installing cli wrapper: {}".format(disco_wrapper))
                self._write_textfile(disco_contents, disco_wrapper)
                disco_wrapper.chmod(0o755)
                print("You can now use the DiscoDOS CLI using ./disco\n")
            # install setup wrapper
            if setup_wrapper.is_file(): # install only if non-existent
                log.info("Config.cli: setup wrapper is already existing: {}".format(
                    setup_wrapper))
            else:
                print("Installing setup wrapper: {}".format(setup_wrapper))
                self._write_textfile(setup_contents, setup_wrapper)
                setup_wrapper.chmod(0o755)
                print("You can now use DiscoDOS setup using ./setup\n")
            # install sync wrapper
            if sync_wrapper.is_file(): # install only if non-existent
                log.info("Config.cli: sync wrapper is already existing: {}".format(
                    sync_wrapper))
            else:
                print("Installing DiscoDOS sync wrapper: {}".format(sync_wrapper))
                self._write_textfile(sync_contents, sync_wrapper)
                sync_wrapper.chmod(0o755)
                print("You can now use DiscoDOS sync using ./sync\n")
            # systemwide installation handling
            if sysinst_sh.is_file(): # install only if non-existent
                log.info("Config.cli: install_systemwide.sh is already existing: {}".format(
                    sysinst_sh))
            else:
                self._write_textfile(sysinst_sh_contents, sysinst_sh)
                sysinst_sh.chmod(0o755)
                hlpmsg ="Execute ./{} for systemwide installation".format(
                    sysinst_sh.name)
                hlpmsg+="\n* makes disco command executable from everywhere."
                hlpmsg+="\n* setup and sync commands still have to be executed "
                hlpmsg+="from inside discodos dir using: "
                hlpmsg+="\n./disco"
                hlpmsg+="\n./sync"
                print_help(hlpmsg)
        elif os.name == "nt":
            if disco_wrapper.is_file(): # install only if non-existent
                log.info("Config.cli: DiscoDOS cli wrapper is already existing: {}".format(
                    disco_wrapper))
            else:
                msg_discoinst = ("\nInstalling DiscoDOS CLI wrapper: {}".format(
                      disco_wrapper))
                print(msg_discoinst)
                log.info(msg_discoinst)
                self._write_textfile(disco_contents, disco_wrapper)
                print_help('Installing DiscoDOS shell: {}'.format(discoshell))
                self._write_textfile(discoshell_contents, discoshell)
                hlpshmsg = 'Usage: '
                hlpshmsg = 'Double click discoshell.bat to open the "DiscoDOS shell," '
                hlpshmsg+= '\nThen put DiscoDOS commands in there.'
                hlpshmsg+= '\nView available commands:'
                hlpshmsg+= '\ndisco -h'
                hlpshmsg+= '\ndisco mix -h'
                hlpshmsg+= '\ndisco search -h'
                hlpshmsg+= '\ndisco suggest -h'
                hlpshmsg+= '\nsetup -h'
                hlpshmsg+= '\nsync -h'
                print_help(hlpshmsg)

    def _posix_wrapper(self, filename, venv_activate, comment):
        '''return some lines forming a basic posix venv wrapper'''
        contents = '#!/bin/bash\n'
        contents+= '{}\n'.format(comment)
        contents+= 'source "{}"\n'.format(venv_activate)
        contents+= '"{}" "$@"\n'.format(filename)
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
        create_msg = '\nCreating config file...'
        log.info(create_msg)
        print(create_msg)
        written = self._write_yaml(config, self.discodos_root / 'config.yaml')
        if written:
            written_msg = 'Now please open the file config.yaml with a '
            written_msg+= 'texteditor and set a value for discogs_token!\n'
            written_msg+= 'Read how to get a Discogs token here: '
            written_msg+= 'https://github.com/JOJ0/discodos#configuring-discogs-api-access\n'
            written_msg+= "Then run setup again!"
            log.info(written_msg)
            print_help(written_msg)

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

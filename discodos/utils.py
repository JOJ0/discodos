from discodos import log
import time
import yaml
from pathlib import Path
import os
import sys

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
        # determine if application is a script file or frozen exe
        if getattr(sys, 'frozen', False):
            self.frozen = True
            log.debug("Config.frozen: Running as a bundled executable.")
            self.discodos_root = Path(os.path.dirname(sys.executable))
        else:
            log.debug("Config.frozen: Running as a Python script.")
            self.frozen = False
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
            if self.frozen: # packaged
                venv_act = False
                disco_py = self.discodos_root / 'cli'
                setup_py = self.discodos_root / 'setup'
                sync_py = self.discodos_root / 'sync'
            else: # not packaged
                venv_act = Path(os.getenv('VIRTUAL_ENV')) / 'bin' / 'activate'
                disco_py = self.discodos_root / 'cli.py'
                setup_py = self.discodos_root / 'setup.py'
                sync_py = self.discodos_root / 'sync.py'

            # cli.py wrapper
            disco_wrapper = self.discodos_root / 'disco'
            disco_contents = self._posix_wrapper(disco_py, venv_act,
                  '# This is the DiscoDOS CLI wrapper.')

            # setup.py wrapper
            setup_wrapper = self.discodos_root / 'discosetup'
            setup_contents = self._posix_wrapper(setup_py, venv_act,
                  '# This is the DiscoDOS setup script wrapper.')

            # sync.py wrapper
            sync_wrapper = self.discodos_root / 'discosync'
            sync_contents = self._posix_wrapper(sync_py, venv_act,
                  '# This is the DiscoDOS sync/backup script wrapper.')

            # install systemwide
            sysinst_sh = self.discodos_root / 'install_wrappers_to_path.sh'
            sysinst_sh_contents = 'echo "Installing disco commands to your user environment..."\n'
            sysinst_sh_contents+= 'mkdir -v ~/bin\n'
            sysinst_sh_contents+= 'cp -v {} ~/bin\n'.format(disco_wrapper)
            sysinst_sh_contents+= 'cp -v {} ~/bin\n'.format(setup_wrapper)
            sysinst_sh_contents+= 'cp -v {} ~/bin\n'.format(sync_wrapper)
            sysinst_sh_contents+= 'echo "Adding $HOME/bin to your PATH by appending a line to $HOME/.bashrc"\n'
            sysinst_sh_contents+= 'echo \'export PATH=~/bin:$PATH\' >> ~/.bashrc\n'
            sysinst_sh_contents+= 'read -p "Reload ~/.bashrc to activate changes? (y/N)" RELOAD\n'
            sysinst_sh_contents+= 'if [[ $RELOAD == "y" || $RELOAD == "Y" ]]; then\n'
            sysinst_sh_contents+= '    source ~/.bashrc\n'
            sysinst_sh_contents+= 'else\n'
            sysinst_sh_contents+= '    exit 0\n'
            sysinst_sh_contents+= 'fi\n'

        elif os.name == 'nt':
            if self.frozen: # packaged
                venv_act = False
                disco_py = self.discodos_root / 'cli.exe'
                setup_py = self.discodos_root / 'setup.exe'
                sync_py = self.discodos_root / 'sync.exe'
            else: # not packaged
                venv_act = Path(os.getenv('VIRTUAL_ENV')) / 'Scripts' / 'activate.bat'
                disco_py = self.discodos_root / 'cli.py'
                setup_py = self.discodos_root / 'setup.py'
                sync_py = self.discodos_root / 'sync.py'

            # WRAPPER cli.py - disco.bat
            disco_wrapper = self.discodos_root / 'disco.bat'
            disco_py = self.discodos_root / 'cli.py'
            disco_contents = self._win_wrapper(disco_py,
                  'rem This is the DiscoDOS cli wrapper.')

            # WRAPPER setup.py - discosetup.bat
            setup_wrapper = self.discodos_root / 'discosetup.bat'
            setup_py = self.discodos_root / 'setup.py'
            setup_contents = self._win_wrapper(setup_py,
                  'rem This is the DiscoDOS setup script wrapper.')

            # WRAPPER sync.py - discosync.bat
            sync_wrapper = self.discodos_root / 'discosync.bat'
            sync_py = self.discodos_root / 'sync.py'
            sync_contents = self._win_wrapper(sync_py,
                  'rem This is the DiscoDOS sync/backup script wrapper.')

            # WRAPPER discoshell.bat
            discoshell = self.discodos_root / 'discoshell.bat'
            if venv_act:
                discoshell_contents = 'start "DiscoDOS shell" /D "{}" "{}"\n'.format(
                    self.discodos_root, venv_act)
            else:
                echo_hints = 'Launch disco.bat to view a usage tutorial'
                discoshell_contents = 'start "DiscoDOS shell" /D "{}" echo "{}"\n'.format(
                    self.discodos_root, echo_hints)
        else:
            log.warn("Config.cli: Unknown OS - not creating CLI wrappers.")
            return True

        # file installation part starts here
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

            # install setup wrapper
            if setup_wrapper.is_file(): # install only if non-existent
                log.info("Config.cli: setup wrapper is already existing: {}".format(
                    setup_wrapper))
            else:
                print("Installing setup wrapper: {}".format(setup_wrapper))
                self._write_textfile(setup_contents, setup_wrapper)
                setup_wrapper.chmod(0o755)
                print("You can now use DiscoDOS setup using ./discosetup\n")

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
                hlpmsg+="\n* setup and sync commands will be available as:"
                hlpmsg+="\ndiscosetup"
                hlpmsg+="\ndiscosync"
                print_help(hlpmsg)
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

            # INSTALL discosetup.bat
            if setup_wrapper.is_file(): # install only if non-existent
                log.info("Config.cli: setup wrapper is already existing: {}".format(
                    setup_wrapper))
            else:
                msg_setupinst = ("Installing DiscoDOS setup wrapper: {}".format(
                      setup_wrapper))
                print(msg_setupinst)
                self._write_textfile(setup_contents, setup_wrapper)
                print("You can now use DiscoDOS setup using discosetup.bat\n")

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
                hlpshmsg+= '\ndiscosetup -h'
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

    def _win_wrapper(self, filename, comment):
        '''return some lines forming a basic windows batch wrapper'''
        contents = '@echo off\n'
        contents+= '{}\n'.format(comment)
        contents+= 'setlocal enableextensions\n'
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
        create_msg = '\nCreating config file...'
        log.info(create_msg)
        print(create_msg)
        written = self._write_yaml(config, self.discodos_root / 'config.yaml')
        if written:
            written_msg = 'Open the file config.yaml using a '
            written_msg+= 'texteditor and set a value for discogs_token!\n'
            written_msg+= 'Read how to get a Discogs token here: '
            written_msg+= 'https://github.com/JOJ0/discodos/blob/master/INSTALLATION.md#configure-discogs-api-access\n'
            written_msg+= "Then re-run DiscoDOS!"
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

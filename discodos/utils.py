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

# util: Discogs: stay in 60/min rate limit
def rate_limit_slow_downer(d_obj, remaining=10, sleep=2):
    if int(d_obj._fetcher.rate_limit_remaining) < remaining:
        log.info("Discogs request rate limit is about to exceed,\
                  let's wait a bit: %s\n",
                     d_obj._fetcher.rate_limit_remaining)
        time.sleep(sleep)

# read yaml
def read_yaml(yamlfile):
    """expects path/file"""
    try:
        with open(str(yamlfile), "r") as fyamlfile:
            return yaml.load(fyamlfile, Loader=yaml.SafeLoader)
    except IOError as errio:
        log.error("Can't find %s.", yamlfile)
        #raise errio
        raise SystemExit(3)
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
        raise SystemExit(3)

class Config():
    def __init__(self):
        discodos_lib = Path(os.path.dirname(os.path.abspath(__file__)))
        self.discodos_root = discodos_lib.parents[0]
        log.info("Config.discodos_root: {}".format(self.discodos_root))
        self.discobase = self.discodos_root / "discobase.db"
        log.info("Config.discobase: {}".format(self.discobase))
        self.conf = read_yaml( self.discodos_root / "config.yaml")
        try: # essential settings
            self.discogs_token = self.conf["discogs_token"]
            self.discogs_appid = self.conf["discogs_appid"]
        except KeyError as ke:
            log.error("Missing key in config.yaml: {}".format(ke))
            raise SystemExit(3)
        try: # optional setting log_level
            self.log_level = self.conf["log_level"]
            log.info("Config.log_level set to {}.".format(
                self.log_level))
        except KeyError:
            self.log_level = "WARNING"
            log.warn("Config.log_level not set, will take from argparser or default.")

    # install cli command (disco) into discodos_root
    def install_cli(self):
        log.info("Config.cli: We are on a {} OS".format(os.name))
        if os.name == "posix":
            disco_file = self.discodos_root / "disco"
            script_contents  = "#!/bin/bash\n"
            script_contents += "# This is the DiscoDOS cli wrapper.\n"
            script_contents += "source ~/.venvs/discodos/bin/activate\n"
            script_contents += "{}/cli.py $@\n".format(self.discodos_root)
            sysinst = self.discodos_root / "install_cli_system.sh"
            sysinst_contents  = "sudo -p \"Need your users password to allow "
            sysinst_contents += "systemwide installation of disco cli command: \" "
            sysinst_contents +=  "cp ./disco /usr/local/bin\n"
        elif os.name == "nt":
            disco_file = self.discodos_root / "disco.bat"
            script_contents  = "rem This is the DiscoDOS cli wrapper.\n"
            script_contents += "{}/cli.py $@\n".format(self.discodos_root)
            sysinst = self.discodos_root / "install_cli_system.bat"
            sysinst_contents = "copy disco.bat c:\windows\system32\n"
        else:
            log.warn("Config.cli: Unknown OS - not creating disco cli wrapper.")
            return True

        if disco_file.is_file():
            log.info("Config.cli: disco cli wrapper is already existing.")
        else:
            print("Creating disco cli wrapper in {}".format(
                self.discodos_root))
            self._write_textfile(script_contents, disco_file)
            self._write_textfile(sysinst_contents, sysinst)
            if os.name == "posix":
                disco_file.chmod(0o755)
                print("You can now use the DiscoDOS cli using ./disco")
                sysinst.chmod(0o755)
            elif os.name == "windows":
                helpmsg  ="You can now use the DiscoDOS cli using disco.bat "
                helpmsg +="(inside this directory!)"
                print_help(helpmsg)
            print_help("Execute {} for systemwide installation.".format(sysinst.name))

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
            raise SystemExit(3)

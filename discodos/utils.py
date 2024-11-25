import logging
import os
import yaml
import re

log = logging.getLogger('discodos')


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
    print('' + str(message) + '\n')


# util: ask user for some string
def ask_user(text=""):
    return input(text)


def read_yaml(yamlfile):
    """expects path/file"""
    try:
        with open(str(yamlfile), "r") as fyamlfile:
            return yaml.load(fyamlfile, Loader=yaml.SafeLoader)
    except IOError:
        log.warning("Can't find %s.", yamlfile)
        # raise errio
        # raise SystemExit(3)
        return False
    except yaml.parser.ParserError:
        log.error("ParserError in %s.", yamlfile)
        # raise errparse
        raise SystemExit(3)
    except yaml.scanner.ScannerError:
        log.error("ScannerError in %s.", yamlfile)
        # raise errscan
        raise SystemExit(3)
    except Exception as err:
        log.error(" trying to load %s.", yamlfile)
        raise err
        # raise SystemExit(3)


def join_sep(iterator, seperator):
    it = map(str, iterator)
    seperator = str(seperator)
    string = next(it, '')
    for s in it:
        string += seperator + s
    return string

def restore_terminal():
    """Executes `reset` on CLI. Use to prevent terminal issues after Textual exit."""
    os.system('reset')


def extract_discogs_id_regex(release_id):
    """Returns the Discogs_id or None."""
    # Discogs-IDs are simple integers. In order to avoid confusion with
    # other metadata plugins, we only look for very specific formats of the
    # input string:
    # - plain integer, optionally wrapped in brackets and prefixed by an
    #   'r', as this is how discogs displays the release ID on its webpage.
    # - legacy url format: discogs.com/<name of release>/release/<id>
    # - legacy url short format: discogs.com/release/<id>
    # - current url format: discogs.com/release/<id>-<name of release>

    for pattern in [
        r"^\[?r?(?P<id>\d+)\]?$",
        r"discogs\.com/release/(?P<id>\d+)-?",
        r"discogs\.com/[^/]+/release/(?P<id>\d+)",
    ]:
        match = re.search(pattern, release_id)
        if match:
            return int(match.group("id"))

    return None

import logging
import os
import re
import yaml
from datetime import datetime

from discogs_client.utils import Condition, Status

log = logging.getLogger('discodos')


RECORD_CHOICES = ["M", "NM", "VG+", "VG", "G+", "G", "F", "P"]
SLEEVE_CHOICES = RECORD_CHOICES + ["generic", "notgraded", "nocover"]
STATUS_CHOICES = ["draft", "forsale", "expired"]

RECORD_CHOICES_RADIO = {
    "M": Condition.MINT, "NM": Condition.NEAR_MINT,
    "VG+": Condition.VERY_GOOD_PLUS, "VG": Condition.VERY_GOOD,
    "+G": Condition.GOOD_PLUS, "G": Condition.GOOD,
    "F": Condition.FAIR, "P": Condition.POOR,
}
SLEEVE_CHOICES_RADIO = RECORD_CHOICES_RADIO | {
        "generic": Condition.GENERIC,
        "notgraded": Condition.NOT_GRADED,
        "nocover": Condition.NO_COVER,
}
STATUS_CHOICES_RADIO = {
    "draft": Status.DRAFT,
    "forsale": Status.FOR_SALE,
    "expired": Status.EXPIRED,
    "pending": "Pending",
    "sold": "Sold",
}
YES_NO_CHOICES_RADIO = {
    True: "Yes",
    False: "No",
}
# Sometimes we need to translate the other way round
RECORD_CHOICES_DISCOGS = {value: key for key, value in RECORD_CHOICES_RADIO.items()}
SLEEVE_CHOICES_DISCOGS = {value: key for key, value in SLEEVE_CHOICES_RADIO.items()}
STATUS_CHOICES_DISCOGS = {value: key for key, value in STATUS_CHOICES_RADIO.items()}


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    except TypeError:
        return False


def print_help(message, _log=False):
    print('' + str(message) + '\n')
    if _log:
        log.debug(message)


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

def timestamp_now():
    return datetime.today().isoformat(" ", "seconds")

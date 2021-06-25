import logging
import yaml

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

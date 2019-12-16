from discodos import log
import time
import yaml

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
        with open(yamlfile, "r") as fyamlfile:
            return yaml.load(fyamlfile, Loader=yaml.SafeLoader)
    except IOError as errio:
        log.warn("Can't find %s \n\n", yamlfile)
        raise errio
        raise SystemExit(3)
    except yaml.parser.ParserError as errparse:
        log.error("ParserError in %s \n\n", yamlfile)
        #raise errparse
        raise SystemExit(3)
    except yaml.scanner.ScannerError as errscan:
        log.error("ScannerError in %s \n\n", yamlfile)
        #raise errscan
        raise SystemExit(3)
    except Exception as err:
        log.error(" trying to load %s \n\n", yamlfile)
        #raise err
        raise SystemExit(3)

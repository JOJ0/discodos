from discodos import log
import time
import discogs_client
import discogs_client.exceptions as errors

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

# connection state class
class conn_state(object):

    def __init__(self):
        self.state = "OFFLINE"
        self.user_wants = "ONLINE"

    def discogs_connect(self):
        userToken = "NcgNaeOXSCgCfBQsaeKhChNXqEQbKaNBQrayltht"
        try:
            global d
            d = discogs_client.Client(
                    "J0J0 Todos Discodos/0.0.1 +http://github.com/JOJ0",
                    user_token=userToken)
            global me
            me = d.identity()
            ONLINE = True
            self.state = "ONLINE"
        except Exception:
            log.error("connecting to Discogs API, let's stay offline!\n")
            ONLINE = False
            self.state = "OFFLINE"
            #raise Exception


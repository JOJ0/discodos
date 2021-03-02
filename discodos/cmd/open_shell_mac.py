
from subprocess import run
#from os import environ, path
from applescript import tell
from discodos.config import Config
import logging

log = logging.getLogger('discodos')


def _run(command):
    #bounds = '{300, 200, 1300, 800}'
    #set bounds of front window to {}
    applescript = '''
                     do script "{}"
                     activate
                  '''.format(command)
    tell.app( 'Terminal', applescript)


def disco():
    #import pdb; pdb.set_trace()
    #MacOS_path = path.split(environ['EXECUTABLEPATH'])[0]
    #command = MacOS_path + '/cli'
    conf = Config(no_create_conf=True)
    conf.install_cli()
    #command = conf.discodos_root / 'cli'
    command = 'disco'  # should be in PATH at this point
    try:
        _run(command)
    except KeyboardInterrupt:
        msg_int = 'DiscoDOS canceled (ctrl-c)'
        print(msg_int)


if __name__ == "__main__":
    disco()
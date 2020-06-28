
from subprocess import run
from os import environ, path
from applescript import tell
from discodos.config import Config


def _run(command):
    tell.app( 'Terminal', 'do script "{}" activate'.format(command))

def disco():
    #import pdb; pdb.set_trace()
    #MacOS_path = path.split(environ['EXECUTABLEPATH'])[0]
    #command = MacOS_path + '/cli'
    #conf = Config()
    conf = Config(no_create_conf=True, no_ask_token=True)
    conf.install_cli(to_path=True)

    command = conf.discodos_root / 'cli'
    _run(command)

#def backup():
#    command = 'discosync -b'
#    _run(command)

if __name__ == "__main__":
    disco()
from discodos.config import Config
import webbrowser

def quickstart():
    webbrowser.open(
        'https://discodos.readthedocs.io/en/latest/QUICKSTART.html'
    )

def manual():
    webbrowser.open(
        'https://discodos.readthedocs.io/en/latest/MANUAL.html'
    )

def configuration():
    webbrowser.open(
        'https://discodos.readthedocs.io/en/latest/INSTALLATION.html#configure-discogs-api-access'
    )

def chart():
    conf = Config()
    webbrowser.open(
        'file://{}'.format(conf.discodos_data / 'discodos_cmds_v0.3_white.png')
    )

if __name__ == "__main__":
    readme()

from discodos.config import Config
import webbrowser

def readme():
    webbrowser.open('https://github.com/JOJ0/discodos/blob/master/README.md')

def manual():
    webbrowser.open('https://github.com/JOJ0/discodos/blob/master/MANUAL.md')

def chart():
    conf = Config()
    webbrowser.open('file://{}'.format(conf.discodos_data / 'discodos_cmds_v0.3_white.png' ))

if __name__ == "__main__":
    readme()
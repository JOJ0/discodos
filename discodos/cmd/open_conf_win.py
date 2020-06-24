from discodos.config import Config
from subprocess import run

def main():
    conf = Config()
    if conf.config_created == True:
        sleep(3)
        echo = "echo Initial DiscoDOS run: A config file was created, click Edit Configuration again"
        #echo = "pause"
        run('start cmd /k {}'.format(echo), shell=True)
    else:
        run('notepad.exe {}'.format(conf.file), shell=True)

if __name__ == "__main__":
    main()
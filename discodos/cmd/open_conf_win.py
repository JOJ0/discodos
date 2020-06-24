from discodos.config import Config
from subprocess import run
from time import sleep

def main():
    conf = Config(no_create_conf=True)
    #if conf.config_created == True:
        #sleep(3)
        #echo = "echo Initial DiscoDOS run: A config file was created, click Edit Configuration again"
        ##echo = "pause"
        #run('start cmd /k {}'.format(echo), shell=True)
    #else:
    # Config class already SystemExists when no config file found
    run('notepad.exe {}'.format(conf.file), shell=True)

if __name__ == "__main__":
    main()
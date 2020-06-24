from subprocess import run

def _run(command):
    run('start /b "DiscoDOS" cmd /k {}'.format(command), shell=True)

def disco():
    command = 'disco'
    _run(command)

def backup():
    command = 'discosync -b'
    _run(command)

if __name__ == "__main__":
    disco()
# DiscoDOS Installation

There are two ways of installing DiscoDOS:

- Release versions (get a program that just works, is easy to install and well tested)
- Development version (get the latest features, contribute to DiscoDOS by trying out new things and reporting back what you think. I usually try to keep things stable in the master branch. I use it myself on my production database, so it just has to work. Seldomely there will be major bugs that really could corrupt our data but in any case make sure you use DiscoDOS' neet built-in backup feature!)


## Release version

...coming soon...

## Development version

DiscoDOS is written entirely in Python. The majority of time, it was coded on a MacOS X 10.13 machine with Python installed via homebrew, thus it's tested well on this platform. There are some users happily using it on Winodws 10 already. I myself also regularily use it on Linux machines too, and it seems to work as good as on my Mac.

Basically it will run on any OS as long as the following prerequisites are met. Please report back in any case, wether it's working fine or you find things that seem unusual on your OS. Thanks a lot!


### Prerequisites

You need to have these software packages installed
* git
* Python version 3.7 or higher

Getting them differs according to your OS

* Most Linux distributions have git and Python available within their package repositories.
* On Windows download from here: https://git-scm.com/download, https://www.python.org/downloads
* On MacOS I suggest getting both packages via homebrew: https://brew.sh/
  (If homebrew seems overkill to you, just use the Windows links above)

Make sure git and python can be executed from everywhere (adjust your PATH environment variable accordingly).

During the Python setup on Windows choose "Customize installation" and select the following options:

- pip
- py launcher
- Associate files with Python (requires the py launcher)
- Add Python to environment variables


### Linux / MacOS

_Skip this chapter if you are on a Windows OS!_

Jump to your homedirectory, clone the repo and double check if the directory discodos has been created.

```
cd
git clone https://github.com/JOJ0/discodos.git
ls -l discodos
```

Create and activate a virtual Python environment! The environment will be saved inside a hidden subfolder of your homedirectory called .venvs/

```
python3 -m venv ~/.venvs/discodos
source ~/.venvs/discodos/bin/activate
```

Double check if your environment is active and you are using the pip binary installed _inside_ your ~/.venvs/discodos/ directory.

`pip --version`

You should see something like this:

`pip 18.1 from /Users/jojo/.venvs/discodos/lib/python3.7/site-packages/pip (python 3.7)`

Install the necessary dependencies into your environment!

`pip install -r ~/discodos/requirements.txt`


### Windows

Please use the regular command prompt window (cmd.exe) and not the "git bash", otherwise the statements using the %HOMEPATH% environment variable won't work! Also note that Windows paths can be written with slashes instead of the usual backslashes these days (putting them inside of quotes is mandatory though!) - in the very unlikely case your Windows version doesn't support this, please just change the paths to use backslashes.

Jump to your homedirectory, clone the repo and double check if the directory discodos has been created.

```
cd %HOMEPATH%
git clone https://github.com/JOJ0/discodos.git
dir discodos
```

Create and activate a virtual Python environment!

```
python -m venv "%HOMEPATH%/python-envs/discodos"
"%HOMEPATH%/python-envs/discodos/Scripts/activate.bat"
```

Double check if your environment is active and you are using the pip binary installed _inside_ your %HOMEPATH%/python-envs/discodos directory.

`pip --version`

You should see something like this:

`pip 19.2.3 from c:\users\user\python-envs\discodos\lib\site-packages\pip (python 3.8)`

Install the necessary dependencies into your environment!

`pip install -r "%HOMEPATH%/discodos/requirements.txt"`

### What now?

Now read on how to set up DiscoDOS on the [README](https://github.com/JOJ0/discodos/blob/master/README.md) page. The next steps would be to configure access to your Discogs collection and initialize the local database.
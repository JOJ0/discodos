# DiscoDOS Installation

There are two ways of installing DiscoDOS:

- Release version (get a program that just works, is easy to install and well tested)
- Development version (get the latest features, contribute to DiscoDOS by trying out new things and reporting back what you think. I usually try to keep things stable in the master branch. I use it myself on my production database, so it just has to work. Seldomely there will be major bugs that really could corrupt your data. In any case make sure you use DiscoDOS' neet built-in backup/sync feature!)


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


### Initialize the database and set up the CLI tools

_Remove the ./ in front of the commands if you are on Windows! Also make sure you have the "py launcher" installed and .py files associated (see setup notes above)._

On first launch, the setup script does several things:

- it creates an empty database -> you should find a file named `discobase.db` in your discodos folder.
- it sets up the DiscoDOS cli
  - Linux/MacOS -> find the files `disco` and `install_cli_system.sh` in your discodos folder.
  - Windows -> find the files `disco.bat` and `discoshell.bat`

Now launch setup and carefully read the output.

`./setup.py`

Hint if setup throws an error: Make sure the python environment you created in the installation instructions above is loaded. On Windows it could happen that *py launcher* is not properly installed - Work around this issue by launching setup.py with python.exe:

`python setup.py`

On **Windows** your starting point to using DiscoDOS is double-clicking `discoshell.bat`. A new command prompt window named "DiscoDOS shell" is opened and the "Virtual Python Environment", DiscoDOS needs to function, is activated. Once inside the shell, execute cli commands via the disco.bat wrapper. As usual on Windows systems you can leave out the .bat ending and just type `disco`.

On **Linux and MacOS** the workflow is slightly different. To execute DiscoDOS cli commands you just type `./disco`. This wrapper script also takes care of activating the "Virtual Python Environment". To conveniently use the `disco` command from everywhere on your system, copy it to a place that's being searched for according to your PATH variable - the provided script `install_cli_system.sh` does this for you and copies it to /usr/local/bin).

_The following commands assume that, depending on your OS, you are either inside the DiscoDOS shell window or `disco` is being found via the PATH variable._

 Check if the database is working by creating a new mix.

`disco mix fat_mix -c`

View your (empty) mix.

`disco mix fat_mix`


### Configure Discogs API access

To access your Discogs collection you need to generate an API login token and put it into the configuration file.

- Login to discogs.com
- Click your avatar (top right)
- Select _Settings_
- Switch to section _Developers_
- Click _Generate new token_
- Open the file `config.yaml` (inside the discodos root dir, next to the files `setup.py` and `cli.py`) and copy/paste the generated Discogs token into it:

 ```
 discogs_token: 'XDsktuOMNkOPxvNjerzCbvJIFhaWYwmdGPwnaySH'
 ```

- Save and close the file

Make sure you are still in the discodos application directory before you move on with setup.

on Linux/Mac

```
cd
cd discodos
```

on Windows

```
cd "%HOMEPATH%"
cd discodos
```


### What now?

Now read on in the [README](https://github.com/JOJ0/discodos/blob/master/README.md) document. The next steps would be to import your Discogs collection and walk through the "Basic Usage Tutorial".
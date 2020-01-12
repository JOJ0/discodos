# The geekiest Vinyl DJ playlist tool on the planet

This tool helps a Vinyl DJ remember and analyze what they played in their sets, or what they could possibly play in the future. It's based on data pulled from one's [Discogs](https://www.discogs.com) records collection.

## Prerequisites

You need to have these software packages installed
* git
* Python version 3.7 or higher

Getting them differs according to your OS

* Most Linux distributions have git and Python available within their package repositories.
* On Windows download from here: https://git-scm.com/download, https://www.python.org/downloads
* On MacOS I suggest getting both packages via homebrew: https://brew.sh/
  (If homebrew seems overkill to you, just use the Windows links above)

Make sure git and python can be executed from everywhere (adjust your PATH environment variable accordingly).

During the Python setup on Windows choose "Customize installation" and make sure you select the following options:

- pip
- py launcher
- Associate files with Python (requires the py launcher)
- Add Python to environment variables

### Linux / MacOS

_Skip this chapter if you are on a Windows OS!_

Clone the github repo

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

Please use the regular command prompt window (cmd.exe) and not the "git bash", otherwise the statements using the %HOMEPATH% environment variable won't work! Also note that Windows paths can be written with slashes instead of the usual backslashes these days - if that's not the case in your Windows version, please just change the paths to use backslashes.

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



## Initial Setup

### Configuring Discogs API access

To access your Discogs collection you need to generate an API login token.

- Login to discogs.com
- Click your avatar (top right)
- Select _Settings_
- Switch to section _Developers_
- Click _Generate new token_
- Create a file named `config.yaml` inside the discodos root dir (next to the files `setup.py` and `cli.py`) that looks like this:

 ```
 ---
 discogs_token: "XDsktuOMNkOPxvNjerzCbvJIFhaWYwmdGPwnaySH"
 discogs_appid: "J0J0 Todos DiscoDOS/0.0.2 +http://github.com/JOJ0"
 log_level: "WARNING"
 ```

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


### Initializing the database and importing your discogs collection 

_Remove the ./ in front of the commands if you are on Windows! Also make sure you have the "py launcher" installed and .py files associated (see setup notes above)._

On first launch, the setup script does several things:

- it creates an empty database -> you should find a file named `discobase.db` in your discodos folder.
- it sets up the DiscoDOS cli
  - Linux/MacOS -> find the files `disco` and `install_cli_system.sh` in your discodos folder.
  - Windows -> find the files `disco.bat` and `discoshell.bat`

Now launch setup and carefully read the output.

`./setup.py`

On **Windows** your starting point to using DiscoDOS is double-clicking `discoshell.bat`. A new command prompt window named "DiscoDOS shell" is opened and the "Virtual Python Environment", DiscoDOS needs to function, is activated. Once inside the shell execute cli commands via the disco.bat wrapper. As usual on Windows systems you can leave out the .bat ending and just type `disco`.

On **Linux and MacOS** the workflow is slightly different. To execute DiscoDOS cli commands you just type `./disco`. This wrapper script also takes care of activating the "Virtual Python Environment". To conveniently use the `disco` command from everywhere on your system, copy it to a place that's being searched for according to your PATH variable - the provided script `install_cli_system.sh` does this for you and copies it to /usr/local/bin).

_The following commands assume that, depending on your OS, you are either inside the DiscoDOS shell window or `disco` is being found via the PATH variable._

 Check if the database is working by creating a new mix.

`disco mix fat_mix -c`

View your (empty) mix.

`disco mix fat_mix`

To let DiscoDOS know about our Discogs record collection we have to import a subset of the available information to the DiscoBASE.

`./setup.py -i`


## Basic Usage

When importing is through, try adding one of your collections tracks to the "mix" you just created.

`disco mix fat_mix -a "Amon Tobin Killer Vanilla"`

Note that even though the tracks name actually is "The Killer's Vanilla" it will be found. If DiscoDOS realizes you are offline it will search in the local DiscoBASE only. Display of search results will vary!

Be precise when asked for the track number on the record: A1 is not the same as A.

View your mix again, your track should be there, verbose mode shows that track and artist names are still missing.

`disco mix fat_mix -v`

Add some more tracks!

Now update your mix's tracks with data pulled from the Discogs API. If track numbers are not precise (eg A vs A1) data won't be found!

`disco mix fat_mix -u`

Use the verbose mode to see all the details pulled from Discogs.

`disco mix fat_mix -v`

Ask what more you could do with your mix and its tracks (short option would be -h)

`disco mix fat_mix --help`

You have two options to edit your mix's tracks. Eg to edit the third track in your mix you could either use

`disco mix fat_mix -e 3`

which edits _all_ fields, or you could select specific fields using the bulk edit option

`disco mix fat_mix -b trans_rating,bpm -p 3`

If you leave out -p 3 (the track position option) you just go through all of your mixes tracks and are asked to put data into the selected fields

`disco mix fat_mix -b trans_rating,bpm`

## Update database from Discogs

You can update your DiscoBASE from your Discogs collection at any time using

`./setup.py -i`

Due to the Discogs API being not the fastest, it quite takes some time though. There are other ways for adding single releases to Discogs AND to your DiscoBASE simultaneously. Check out the command below. First of all notice that we are in "mix mode" and use the -a option to add a release/track to a mix from there. Then, instead of searching for a text-term we hand over a Discogs release ID. DiscoDOS will look for this exact release ID and add it to your Discogs collection as well as to the local DiscoBASE.

`disco mix fat_mix -a 123456`

To add a release to your local database **only** (because it's been already added to your collection via the Discogs web interface) you just use the import command in the setup script with a release ID attached.

`./setup.py -i 123456`
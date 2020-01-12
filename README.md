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

Double check if your environment is active and you are using the pip binary installed inside your ~/.venvs/discodos/ directory.

`pip --version`

(You should see something like this)
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

- it creates an empty database -> You should find a file named `discobase.db` in your discodos folder.

`./setup.py`

 Check if the database is working by creating a new mix.

`./cli.py mix -c new_mix_name`

View your mix.

`./cli.py mix new_mix_name`

Import your collection to the DiscoBASE

`./setup.py -i`


## Usage

When the import is through you should be able to add your collection's tracks to the "mix" created above.

`./cli.py mix new_mix_name -a "Amon Tobin Killer Vanilla"`

Note that even though the tracks name actually is "The Killer's Vanilla" it will be found.

Be precise when asked for the track number on the record: A1 is not the same as A.

View your mix again, your track should be there, verbose mode shows that track and artist names are still missing.

`./cli.py mix new_mix_name -v`

Add some more tracks!

Now update your mix's tracks with data pulled from the Discogs API. If track numbers are not precise (eg A vs A1) data won't be found!

`./cli.py mix new_mix_name -u`

Use the verbose mode to see all the details pulled from Discogs.

`./cli.py mix new_mix_name -v`

Ask what more you could do with your mix and its tracks

`./cli.py mix new_mix_name --help`

You have two options to edit your mix's tracks. Eg to edit the third track in your mix you could either use

`./cli.py mix new_mix_name -e 3`

which edits _all_ fields, or you could select specific fields using the bulk edit option

`./cli.py mix new_mix_name -b trans_rating,bpm -p 3`

If you leave out -p 3 (the track position option) you just go through all of your mixes tracks and are asked to put data into the selected fields

`./cli.py mix new_mix_name -b trans_rating,bpm`

## Update database from Discogs

You can update your DiscoBASE from your Discogs collection at any time using

`./setup.py -i`

Due to the Discogs API being not the fastest this takes quite some time though. There are other ways for adding single releases to Discogs AND to your DiscoBASE simultaneously. Check out the command below. First of all notice that we are in "mix mode" and use the -a option to add a release/track to a mix from there. Then, instead of searching for a text-term we hand over a Discogs release ID. DiscoDOS will look for this exact release ID and add it to your Discogs collection as well as to the local DiscoBASE.

`./cli.py mix new_mix_name -a 123456`

To add a release to your local database **only** (because it's been already added to your collection via the Discogs web interface) you just use the import command in the setup script with a release ID attached.

`./setup.py -i 123456`
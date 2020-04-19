# DiscoDOS Manual
```
                _______  _______ ________
               /       \        /       /
              /  ___   /  ___  /  _____/
             /  /  /  /  /  /  \____  \
            /  /__/  /  /__/  _____/  /
D i s c o  /                /        /  - The geekiest DJ tool on the planet
          /_______/\_______/________/
```
helps a DJ remember and analyze what they played in their sets, or what they could possibly play in the future. It's based on data pulled from a [Discogs](https://www.discogs.com) record [collection](https://support.discogs.com/hc/en-us/articles/360007331534-How-Does-The-Collection-Feature-Work-). Releases and tracks can be matched and linked with the [MusicBrainz](https://musicbrainz.org) database and thus receive additional data like BPM or musical key from [AcousticBrainz](https://acousticbrainz.org), a "crowd source based acoustic information database". 

DiscoDOS primarily aims at the Vinyl DJ but features for "Hybrid-Vinyl-Digital-DJs" like linking a Discogs collection to DJ software (eg Pioneer's Rekordbox) are planned. DiscoDOS will then be able to answer questions like: "Do I have all those records in this particular set in digital format too, so I could play it in a digital-only situation?". Further feature plans include built-in contribution possibilites to AcousticBrainz, to help this useful resource grow.

DiscoDOS currently is available as a command line tool only, though prototypes of a mobile and a desktop app exist already. Despite what the name implies it follows most standards of a typical shell utility you would find on a [UNIX-like operating system](https://en.wikipedia.org/wiki/Unix-like). It is aimed to support modern Linux, MacOS and Windows systems. This is how it looks like:

FIXME

### Installation

Please head over to the [INSTALLATION](https://github.com/JOJ0/discodos/blob/master/INSTALLATION.md) document for step by step instructions on how to get DiscoDOS running on your machine.


### Configuring Discogs API access

To access your Discogs collection you need to generate an API login token.

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


### Initializing the database and setting up the cli tools 

_Remove the ./ in front of the commands if you are on Windows! Also make sure you have the "py launcher" installed and .py files associated (see setup notes above)._

On first launch, the setup script does several things:

- it creates an empty database -> you should find a file named `discobase.db` in your discodos folder.
- it sets up the DiscoDOS cli
  - Linux/MacOS -> find the files `disco` and `install_cli_system.sh` in your discodos folder.
  - Windows -> find the files `disco.bat` and `discoshell.bat`

Now launch setup and carefully read the output.

`./setup.py`

On **Windows** your starting point to using DiscoDOS is double-clicking `discoshell.bat`. A new command prompt window named "DiscoDOS shell" is opened and the "Virtual Python Environment", DiscoDOS needs to function, is activated. Once inside the shell, execute cli commands via the disco.bat wrapper. As usual on Windows systems you can leave out the .bat ending and just type `disco`.

On **Linux and MacOS** the workflow is slightly different. To execute DiscoDOS cli commands you just type `./disco`. This wrapper script also takes care of activating the "Virtual Python Environment". To conveniently use the `disco` command from everywhere on your system, copy it to a place that's being searched for according to your PATH variable - the provided script `install_cli_system.sh` does this for you and copies it to /usr/local/bin).

_The following commands assume that, depending on your OS, you are either inside the DiscoDOS shell window or `disco` is being found via the PATH variable._

 Check if the database is working by creating a new mix.

`disco mix fat_mix -c`

View your (empty) mix.

`disco mix fat_mix`

### Importing your Discogs collection

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
<!-- omit in toc -->
# Manual

This document contains in-detail explanations about a lot but not all you can do with DiscoDOS.

## General things about command line tools

In case you don't use command line tools much: `dsc` is designed as such and thus each option has a short form and a long form. For example the help output of the dsc main command can be written two ways:

`dsc --help` or `dsc -h`

another example:

`dsc suggest --bpm 123` is the same as `dsc suggest -b 123`

Throughout this section, mostly the short forms are used, but sometimes the long forms too because they're just more self-explanatory.

Also a common concept with command line tools is that "optional arguments" (the ones starting with a dash) can be put before or after "positional arguments (in this case the mix_name):

`dsc mix new_mix -c` is the same as `dsc mix -c new_mix`

Also the order of "optional arguments" is freely choosable most of the time:

`dsc search "search terms" -m new_mix -t A2`

is the same as

`dsc search "search terms" -t A2 -m new_mix `



## *dsc* - the main command

DiscoDOS' main command is `dsc`, to view it's help:

`dsc -h`

It contains several subcommands or further command groups.

To execute a subcommand you would eg type:

`dsc search ...`

Each subcommand has its own built-in help output:

``` bash
dsc mix -h
dsc suggest -h
dsc import -h
dsc import basic -h
dsc import tracks -h
dsc import release -h
dsc import sales -h
dsc import listing -h
dsc clean -h
dsc clean collection -h
dsc clean sales -h
dsc search -h
dsc sell -h
dsc stats -h
dsc ls -h
dsc links -h
```

The following chapters describe some features of the respective commands, an exhaustive list is found in the [Commands Reference](index_commands_reference.rst)

### Global switches

The general behaviour of `dsc` can be altered by some "optional arguments":

Enable INFO logging output or DEBUG logging output on your terminal (usually only relevant if you're investigating errors, are a developer or just want to know what DiscoDOS is doing under the hood):

enable INFO logging (-v) or DEBUG logging (-vv) output:

`dsc -v ...` or `dsc -vv ...`

DiscoDOS checks if it's online automatically but can be forced to stay in offline mode:

`dsc -o ...`




## The *dsc* subcommands

Each subcommand has its typical purpose but some actions can be executed from within other subcommands as well.

### Abbreviations

`dsc` commmands can be abbreviated. For example to issue `dsc import release` use `dsc imp rel` or even `dsc i r`.


### The *mix* command

A mix is basically just a list of tracks in a specific order, a playlist, a track pool, you name it.

Create a mix. You will be asked to put in general info about the mix (venue, last played date). Make sure the played date is in the format YYYY-MM-DD:

`dsc mix my_mix -c`

Delete a mix (yes, it's a capital D):

`dsc mix my_mix -D`

Copy a mix. You will be asked for the name of the copy. (Note: --copy doesn't have a short form option):

`dsc mix my_mix --copy`

Edit general mix info (venue, played date):

`dsc mix my_mix -E`

Add a track to a mix. You will be asked for the track number on the found release. Note: Tracks can be added using the [search command](#search-action-add-track-to-mix) as well:

`dsc mix my_mix -a "search terms"`

To add the track at a specific position in the mix, rather than at the end:

`dsc mix my_mix -a "search terms" -p 3`

Edit details or 3rd track in the mix (key, key_notes, BPM, transition rating, transition notes, track notes, position in the mix, track number on the record, custom MusicBrainz recording ID):

`dsc mix my_mix -e 3`

Delete 3rd track in the mix:

`dsc mix my_mix -d 3`

Bulk-edit selected fields of all tracks in a mix. You can cancel editing without data loss by pressing ctrl-c. Data is saved after each track.

`dsc mix my_mix -b trans_rating,bpm,key`

Available field names: *key,bpm,track_no,track_pos,key_notes,trans_rating,trans_notes,notes,m_rec_id_override* (_**Make sure your field list has only commas and no spaces in between!**_)

To start bulk-editing at a specific track position rather than at track 1:

`dsc mix my_mix -b trans_rating,bpm,key -p 3`

Get track names for whole mix from Discogs:

`dsc mix my_mix -u`

Start getting track names at position 3 in the mix, rather than at track 1:

`dsc mix my_mix -u -p 3`

Get additional track info for whole mix from MusicBrainz/AcousticBrainz (key, bpm, links):

`dsc mix my_mix -z`

Start getting MusicBrainz/AcousticBrainz info at position 3 in the mix, rather than at track 1:

`dsc mix my_mix -z -p 3`

Run a "detailed *Brainz match" (more likely to find matches but significantly slower)

`dsc mix my_mix -zz`

Get track names for _all_ tracks in _all_ mixes from Discogs:

`dsc mix -u`

Get MusicBrainz/AcousticBrainz info for _all_ tracks in _all_ mixes from Discogs. Do a "detailed *Brainz match" run:

`dsc mix -zz`

*Brainz matching is a tedious process for DiscoDOS (more details on this [here](#the-import-command-group)), if you have to switch off your computer for any reason while it's running, cancel the process using ctrl-c and it later at the given position (in this example track number 150 in the list of *all* tracks in *all* mixes):

`dsc mix -zz --resume 150`





### The *suggest* command

The suggest command helps a DJ find possible track combinations by reporting how a track has been used in the past or by finding tracks fitting with certain criteria. Fun fact: These features were the initial ideas for writing a program like DiscoDOS.

Find out in which combinations a track ever was played by looking through all your mixes. This command does a regular search in the collection, spits out a "first match" release and asks for a track number on the release. The presented output shows "snippets" of mixes, telling you exactly which tracks you have used _before_ and _after_ the selected track:

`dsc suggest "amon tobin kitchen sink"`


Show all tracks in collection _**containing**_ "Dm" (D minor) either in the user-key or AcousticBrainz keys fields (key, chords_key).

`dsc suggest -k Dm`

DiscoDOS allows a user to put in more than one key in the user-key field. Information like "Am/Dm/Gm" is allowed. To find this information the following search could be used. Note the _wildcard_ character being the percent sign (%):

`dsc suggest -k "Am%Gm"`

Certainly the a record with "Am/Dm/Gm" in the user-key field would also be found by a simple search like this:

`dsc suggest -k Am`


Find all tracks in collection with a BPM _**around**_ 120. The pitchrange of a typical turntable is taken into account. Currently this is hardcoded to +/-6 percent (this will be a user-configurable value in future DiscoDOS versions):

`dsc suggest -b 120`

key and BPM search can be combined:

`dsc suggest -k Dm -b 120`


**Note: The key and BPM suggest commands require sufficient information in the DiscoBASE. Either in the user-editable key and BPM fields or in the AcousticBrainz fields**

Read how to automatically fill these fields with data from AcousticBrainz in the following section about the [import command](#the-import-command-group).




### The *import* command group

#### Importing releases / collection items

You can update your DiscoBASE from your Discogs collection at any time, if data is already existing, it will be updated.
Due to the Discogs API being not the fastest, it takes some time though. There are other ways for adding single releases to Discogs AND to your DiscoBASE simultaneously.

_**Note: This imports all your releases, but not the tracks on them**_

`dsc import basic`

A quicker alternative, if you are about to import just a couple of new releases is to use the -a option. The release will be added to your Discogs collection _and_ also imported to DiscoBASE. Pass the release ID or the URL of the release (eg https://www.discogs.com/release/123456) .

_**Note: You don't have to click "Add to Collection" on discogs.com, DiscoDOS does this for you**_

`dsc import release -a 123456`

To add a release to DiscoBASE **only** (because it's been already added to your collection via the Discogs web interface), just use the import command with a release ID or URL attached: 

`dsc import release 123456`

To remove a release:

`dsc import release -d 123456`



#### Importing track details

To import all releases including all tracks in your collection use the tracks subcommand. 1000 records take about 20-30 minutes to import:

`dsc import tracks`

To add additional data to your tracks from MusicBrainz/AcousticBrainz (key, BPM, links) use the brain subcommand. Your releases will then be "matched" one-by-one with MusicBrainz - this is not the easiest task for DiscoDOS, several things have to be "tried" to get it right. Differences in spelling/wording of catalog number, artists, title, track numbers, track names in MusicBrainz compared to Discogs are the main reason why it takes that long:

_**Note: This process will take hours. Best you let it run "overnight"**_

`dsc import brainz`

A slightly quicker but less effective method is using the --quick option:

`dsc import brainz -q`

Also remember that it's unlikely that MusicBrainz even *has* an entry for each of your records. Discogs still *is* the most complete music database on earth compared to others. Most definitely when it comes to Vinyl records.

Also note that often it happens that a MusicBrainz track _can_ be "matched" but AcousticBrainz does not have an entry for it yet.

If for some reason you can't complete the run (connection problems, having to switch off your computer, ...) you can resume the process at a later time. DiscoDOS spits out regularly how many tracks have been matched already and how many are to be done. This will resume the matching at track number 2500 in your collection:

`dsc import brainz --resume 2500`

The "*Brainz match process" currently adds the following data to releases:

- Release MusicBrainz ID (Release MBID)
- weblink to the MusicBrainz release

and the following data to tracks (if available):

- BPM
- key
- chords key
- Recording MusicBrainz ID (Recording MBID)
- weblink to the MusicBrainz recording (A track is called a recording in "MusicBrainz speak")
- weblink to the AcousticBrainz recording (AcousticBrainz uses the same recording MBID as MusicBrainz - this is the link between the two services!)


#### Importing Marketplace inventory items

The whole inventory:

`dsc import sales`

Single sales listings:

`dsc import listing <listing_id>`




### The *search* command

#### Online search

As the name implies, this command searches in your collection. **By default it uses the Discogs API to search for release names, track names, track artists, catalog numbers and labels.**, and then compares those results with your local collection data in the DiscoBASE. This is an efficient way, that makes use of the versatile Discogs search without having to reinvent the wheel.

Let's try a search:

`dsc search "Amon Tobin"`

_**Note: The online search is designed "first match"**_

So this gives you the first found "Amon Tobin" album in your collection only. You have to be more specific to find a particular album:

`dsc search "Amon Tobin Foley Room"`

#### Offline search

If you currently are not connected to the internet or you enable "offline mode" the *search* command behaves differently: Your search terms are only applied against the *release title* and the *release artist(s)*, but not the *track name*. There is a reason for this: DiscoDOS by default does not import *track name*. Even though certainly you have the option to import *track names*, the search does not rely on this. Maybe this behaviour changes in future releases. It was a design decision in the first DiscoDOS prototype versions.

_**Note: The offline search shows a "list of matching items"**_

#### *search* command actions

To "do" something with a track on an album you need to append an "optional argument" to the command. The following actions can be applied to the found track:

- "edit track" (option -e)
- "add track to mix" (option -m)
- "update from Discogs" (option -u)
- "update from *Brainz" (option -z)

#### *search* action "edit track"

To edit the track's details in the DiscoBASE you use:

`dsc search "Amon Tobin Foley Room" -e`

You will see the album's contents and be asked to put in a track number (eg A1, C2, ...). Then you will be walked through all the "editable" fields. It's pretty self-explanatory, but read the hints on the screen.

If you know which track number you'd like to edit already, provide it on the command line directly. You won't be asked for the track number then:

`dsc search "Amon Tobin Foley Room" -e -t B2`

#### *search* action "add track to mix"

The track you select on the found release will be added to the given mix-name:

`dsc search "Amon Tobin Foley Room" -m my_mix`

If your mix's name contains spaces, wrap it in double quotes:

`dsc search "Amon Tobin Foley Room" -m "my longish mix name"`

As a shortcut you can always just use the mix's ID number (you see the numbers in the output of the `dsc mix` command):

`dsc search "Amon Tobin Foley Room" -m 27`

Certainly also here you can provide the track number on the command line already. So to add track A2 on "Foley Room" to mix number 27:

`dsc search "Amon Tobin Foley Room" -m 27 -t A2`

#### *search* action "update from discogs"

As already mentioned already, DiscoDOS is minimalistic by default. The default import command `dsc import` just gets exactly this data from Discogs: release IDs, release titles, release artists, catalog numbers. To put track names of a particular track into the DiscoBASE as well you'd use:

`dsc search "Amon Tobin Foley Room" -u`

Again, combination with -t is possible:

`dsc search "Amon Tobin Foley Room" -u t A2`

To make **all** *track names* on **all** releases in your collection available offline, use:

`dsc search all -u`

_**Note: This is exactly the same as using `dsc import --tracks` or in short: `dsc import -u`.**_

Read more on importing release and track information in the [import command section](#the-import-command-group)

#### *search* action "update from *Brainz"

To extend a tracks information with data from MusicBrainz and AcousticBrainz:

_**Note: To make this work, the track must have been updated from Discogs with track names already. See [update from Discogs](#search-action-update-from-discogs) action above.**_

`dsc search "Amon Tobin Foley Room" -z`

If the track couldn't be matched with the regular match command, try the "detailed match" command (takes more time, but chances on finding a match are higher):

`dsc search "Amon Tobin Foley Room" -zz`

or as usual with track name already in the command:

`dsc search "Amon Tobin Foley Room" -zz -t A2`

If you've already imported all your *track's names* to the DiscoBASE, you could even try to update **all** tracks with MusicBrainz information (takes a couple of hours):

```
dsc search all -z
dsc search all -zz
```

Read more on the performance of the *Brainz match process and what exactely it imports in the [import command section](#the-import-command-group)




## _discosync_ - The DiscoDOS backup & sync tool

`discosync` is used to save the DiscoBASE to the cloud and restore it if something went wrong. It also can be used to share it between multiple computers. There are currently two options, for storing the backups:

* Dropbbox
* A folder on a webserver

A little configuration hast to be done. Follow the steps in the [Dropbox configuration chapter](INSTALLATION.md#configure-dropbox-access-for-discosync) or the [Webserver configuration chapter](INSTALLATION.md#configure-a-webserver-folder-for-discosync)


Depending of your chosen way of saving backups you have to launch `discosync` differently; Option -t selects which type of storage should be accessed:

```
discosync -t dropbox ...
discosync -t webdav ...
```

The "types" can be abbreviated:

```
discosync -t d ...
discosync -t w ...
```


### Backup

The backup command is straight forward and does not require any user-interaction after launching:

To backup to your **Dropbox**:

`discosync -t d --backup`

or use its short form: `discosync -t d -b`

Dropbox currently is the hardcoded **default** "storage type", so actually it's sufficient to run:

`discosync -b`

_**Note: The default backup storage type might be configurable in future DiscoDOS releases**_

To backup to a **WebDAV folder**:

`discosync -t w --backup`

short form: `discosync -t w -b`


### Viewing existing backups

Dropbox:

`discosync --show`

or short: `discosync -s`

WebDAV:

`discosync -t w --show`

or: `discosync -t w -s`


### Restore

Restoring your database from a backup is an interactive process - you will be asked which backup you'd like to restore and warned that your local discobase.db file would be overwritten.

Dropbox:

`discosync --restore`

or short: `discosync -r`

WebDAV:

`discosync -t w --restore`

or short: `discosync -t w -r`
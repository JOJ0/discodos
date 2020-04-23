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
helps a DJ remember and analyze what they played in their sets, or what they could possibly play in the future. It's based on data pulled from a users [Discogs](https://www.discogs.com) record [collection](https://support.discogs.com/hc/en-us/articles/360007331534-How-Does-The-Collection-Feature-Work-). Tracks can be organized into playlists and mix-transitions rated. Additionally the collection can be linked to the online music information services [MusicBrainz](https://musicbrainz.org) and [AcousticBrainz](https://acousticbrainz.org), thus further information (like musical key and BPM) is made available to the user.

DiscoDOS primarily aims at the Vinyl DJ but features for "Hybrid-Vinyl-Digital-DJs" like linking the Discogs collection to DJ software (eg Pioneer's Rekordbox) are planned. DiscoDOS will then be able to answer questions like: "Do I have all those records in this particular set in digital format too, so I could play it in a digital-only situation?". Further feature plans include built-in contribution possibilites to [AcousticBrainz](https://acousticbrainz.org) (a crowd source based acoustic information database), to help this useful resource grow.

DiscoDOS currently is available as a command line tool only, though prototypes of a mobile and a desktop app exist already. Despite of what the name implies, it's just the look that is reminiscent of the 80s/90s operating system, its usability follows most standards of a typical [shell](https://en.wikipedia.org/wiki/Shell_(computing)#Unix-like_systems) utility you would find on a [UNIX-like operating system](https://en.wikipedia.org/wiki/Unix-like). It is aimed to support modern Linux, MacOS and Windows systems.

This should give you an idea on how it looks and feels (your screen is not broken, these animated gifs are very low quality to make them load quickly):

##### Viewing mix details, searching and adding track:
![demo gif 1](assets/intro_gif_v0.4_1-580_16col_960x600.gif)
##### Updating track information from Discogs and MusicBrainz/AcousticBrainz:
![demo gif 2](assets/intro_gif_v0.4_580-end_16col_960x600.gif)

## Installation

Please head over to the [INSTALLATION](https://github.com/JOJ0/discodos/blob/master/INSTALLATION.md) document for step by step instructions on how to get DiscoDOS running on your machine.


## Importing your Discogs collection

To let DiscoDOS know about our Discogs record collection we have to import a subset of the available information to the DiscoBASE.

`disco import`


## Basic Usage Tutorial

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

## Common Workflows

### Import/Update from Discogs

You can update your DiscoBASE from your Discogs collection at any time, if data is already existing, it will be updated.

`disco import`

Due to the Discogs API being not the fastest, it quite takes some time though. There are other ways for adding single releases to Discogs AND to your DiscoBASE simultaneously. Check out the command below. First of all notice that we are in "mix mode" and use the -a option to add a release/track to a mix from there. Then, instead of searching for a text-term we hand over a Discogs release ID. DiscoDOS will look for this exact release ID and add it to your Discogs collection as well as to the local DiscoBASE.

`disco mix fat_mix -a 123456`

An alternative, if you are not about to add this new release to a mix and just want to add it to Discogs collection _and_ to the DiscoBASE (to have it available for future mixes) you can use the -a option whith the import subcommand:

`disco import -a 123456`

To add a release to DiscoBASE **only** (because it's been already added to your collection via the Discogs web interface) you just use the import command in the setup script with a release ID attached. (Sidenote: Unfortunately this way it takes significantly longer because of drawbacks in how the API is accessible via the API):

`disco import 123456`


## Command Reference

This section is an in-detail explanation about everything you can do with DiscoDOS. If you'd like to see how to do typical day to day tasks, jump to the [Common Workflows](#Common-Workflows) section, and come back here later.

### General things about command line tools

In case you don't use command line software much: `disco` is designed like a typical command line utiltiy and thus each option has a short form and a long form. For example the help output of the disco main command can be written two ways:

`disco --help`

or

`disco -h`

another example:

`disco suggest --bpm 123`

is the same as

`disco suggest -b 123`

Throughout this command reference section, I will mostly use the short forms, but sometimes the long form as well because it's just more self-explanatory.

### *disco* command

DiscoDOS' main command is `disco`, to view it's help:

`disco -h`

`disco` consists of several subcommands, namely:

- search
- mix
- suggest
- import

To execute a subcommand you would eg type:

`disco search ...`

Each subcommand has its own built-in help output:

```
disco search -h
disco mix -h
disco suggest -h
disco import -h
```

## *disco* global switches

The general behaviour of `disco` can be altered by some switches:

Enable INFO logging output or DEBUG logging output on your terminal (usually only relevant if you're investigating errors, are a developer or just want to know what DiscoDOS is doing under the hood):

enable INFO logging output:

`disco -v ...`

or to enable DEBUG output too:

`disco -vv ...`

Stay in offline mode:

`disco -o ...`

## The *disco* subcommands

Each subcommand has it's typical purpose but note that some actions can be executed from more than one subcommend because it makes sense.

### The *search* command

As the name implies, this command can searches in your collection. By default it uses the Discogs API to search for release names, track names, track artists, catalog numbers and labels.

To search an album of artist "Amon Tobin" you would type:

`disco search "Amon Tobin Foley Room"`

You will see the Album's details and its contents.

**Note: The online search is designed to just show you the "first match" it finds**

So if you'd just put in an artist name as the search term, you will see the first found album of this artist only:

`disco search "Amon Tobin"`

So you have to be more specific in your search terms to find a particular album (as shown in the first example in this section)

If you currently are not connected to the internet or you enable the "offline mode" the *search* command behaves differently: Your search terms are only applied against the *release title* and the *release artist(s)*, but not the *track name*. There is a reason for this: DiscoDOS by default does not import *track name*. Even though certainly you have the option to import *track names*, the search does not rely on this. Maybe this behaviour changes in future releases. It was a design decision in DiscoDOS first prototype version.

**Note: The offline search shows a "list of matching items"**

#### *search* command actions

To "do" something with a track on the album you need to append "optional arguments" to the command, in short "options". This options will apply several actions on the found item(s). There are four actions available:

- "edit track" (-e)
- "add track to mix" (-m)
- "update from Discogs" (-u)
- "update from *Brainz" (-z)

#### *search* "edit track" action

To edit the tracks details in the DiscoBASE you use:

`disco search "Amon Tobin Foley Room" -e`

You will see the albums contents and be asked to put in a track number (eg A1, C2, ...). Then you will be walked through all the "editable" fields. It's pretty self-explanatory, but read the suggestions on the screen.

If you know which track number you'd like to edit already, provide it on the command line already. You won't be asked for the track number then:

`disco search "Amon Tobin Foley Room" -e -t B2`

#### *search* "add track to mix" action

The track you select on the found release will be added to the given mix-name:

`disco search "Amon Tobin Foley Room" -m my_mix`

If your mix's name contains spaces, wrap it in double quotes:

`disco search "Amon Tobin Foley Room" -m "my longish mix name"`

As a shortcut you can always just use the mix's ID number (you see the numbers in the output of the `disco mix` command):

`disco search "Amon Tobin Foley Room" -m 27`

Certainly also here you can provide the track number on the command line already. So to add track A2 on "Foley Room" to mix number 27:

`disco search "Amon Tobin Foley Room" -m 27 -t A2`

#### *search* "update from discogs" action

As already mentioned already, DiscoDOS is minimalistic by default. The default import command `disco import` just gets exactly this data from Discogs: release IDs, release titles, release artists, catalog numbers. To put track names of a particular track into the DiscoBASE as well you'd use:

`disco search "Amon Tobin Foley Room" -u`

Again, combination with -t is possible:

`disco search "Amon Tobin Foley Room" -u t A2`

**Note: Having track names in the DiscoBASE is a prerequisite to use the "update from *Brainz" action.**

To make **all** *track names* on **all** releases in your collection available offline, use:

`disco search all -u`

**Note: This is exactley the same as using `disco import --tracks` or in short: `disco import -u`.**

#### *search* "update from brainz" action

To extend a tracks information with data from MusicBrainz and AcousticBrainz:

`disco search "Amon Tobin Foley Room" -z`

Matching a track out of your Discogs collection with a track in MusicBrainz is a tedious job for DiscoDOS and takes time (it has to search and compare a lot of things - differences in spelling/wording in catalog numbers, track names, artist names - just to name a few - cause the matching process to take its time).

If you didn't find the track's name with the regular match command, try the "detailed match" command (It takes even more time, but gives more results):

`disco search "Amon Tobin Foley Room" -zz`

or as usual with track name already in the command:

`disco search "Amon Tobin Foley Room" -zz -t A2`

Currently the following data will be put in the DiscoBASE for the given track(s): 

- BPM
- key
- chords key
- Release MusicBrainz ID (Release MBID)
- Recording MusicBrainz ID (Recording MBID)
- weblink to the MusicBrainz release
- weblink to the MusicBrainz recording (A track is called a recording in "MusicBrainz speak")
- weblink to the AcousticBrainz recording (AcousticBrainz uses the same recording MBID as MusicBrainz - this is the link between the two services!)

If you've already imported all your *track's names* to the DiscoBASE, you  could even try to update **all** tracks with MusicBrainz information:




### The *mix* command

### The *suggest* command

### The *import* command



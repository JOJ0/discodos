<!-- omit in toc -->
# Quickstart

## Installation

Please head over to the [INSTALLATION](INSTALLATION.md) document for step by step instructions on how to get DiscoDOS running on your machine.



## Importing your Discogs collection and Marketplace inventory

To let DiscoDOS know about our Discogs record collection we have to import a subset of the available information to the local database (the so-called DiscoBASE).

`dsc import basic`

`dsc import sales`



## Basic Usage Tutorial - Mixes

When importing is through, create a new mix:

`dsc mix my_mix -c`

View your (empty) mix:

`dsc mix my_mix`

Try adding one of your collection's tracks to the "mix" you just created.

`dsc mix my_mix -a "Amon Tobin Killer Vanilla"`

If DiscoDOS realizes you are offline it will search in the local database only. Only online search understands track names, offline search doesn't, it needs artists and/or release names. Learn why, further below.

Be precise when asked for the track number on the record: A1 is not the same as A.

View your mix again, your track should be there. verbose view (-v) shows that track and artist names are still missing because DiscoDOS by default is minimalistic - the initial import command did not fetch this data yet:

`dsc mix my_mix -v`

Add some more tracks!

Now get track artist/titles for all the tracks in the mix. If track numbers are not precise (eg A vs A1) data won't be found!

`dsc mix my_mix -u`

Use the verbose mode to see all the details pulled from Discogs:

`dsc mix my_mix -v`

Ask what more you could do with your mix and its tracks (short option would be -h):

`dsc mix my_mix --help`

Edit details of the third track in your mix:

`dsc mix my_mix -e 3`

There is also a bulk-edit option to edit specific fields of all tracks in the mix. Read about it in the command reference section of [The mix command](MANUAL.md#the-mix-command)

Get additional data about your mix's tracks from MusicBrainz and AcousticBrainz (key, BPM, links):

`dsc mix my_mix -zz`

Read more about the *Brainz update process here: [The import command](MANUAL.md#the-import-command-group)



## Common Tasks

This section guides you through typical DiscoDOS workflows. If you would rather like to read an in-detail explanation of what each command does, go to the [DiscoDOS User's Manual](MANUAL.md).

### I'd like to sell records

Make sure your local sales inventory is up to date:

`dsc import sales`

List a record for sale with the "sell wizard". Don't pass the `-p/--price` option! You'll receive price suggestions and will be prompted to accept or adjust the recommendations interactively.

`dsc sell -a forsale -c NM`

_**Note: The sell command has some built-in defaults, most importantly `VG+` for `-c/--condition` and `draft` for the `-a/--status` option. Defaults are documented in [the command's online help](dsc.rst).**_

To edit existing sales listings, use the DiscoDOS TUI command `dsc ls`:

`dsc ls artist=squarepusher`

_**Note: `dsc ls` lists records in a fancy graphical but still text-based user interface. Use shortcut `e` to edit a sales listing. Further helpful shortcuts are `v` display video links and `return` to fetch marketplace stats and price suggestions.**_



### What's the quickest way to document a mix?

DiscoDOS can best help you when it's feeded with as much of your DJ'ing habits as possible. Writing down a mix is done in a matter of minutes. Best you listen through a mix recording while having your records near you. Certainly a mix does not have to be a complete DJ set, it could just be some track combinations you like to play recently. Let's get started by creating a new mix:

`dsc mix my_mix -c`

The easiest command to remember for adding tracks to the mix is this one:

`dsc mix my_mix -a "artist title album"`

If you hold the record in your hand and know exactly what track it is you played, the quickest way would be using the search subcommand, because the tracknumber on the record (A, B, A1, A2, etc.) can be given directly in the command. This spares you the question of which track on the record you'd like to add:

`dsc search "artist title album" -m my_mix -t A2`

_**Note: Your search terms don't have to include artist, title and album. Also label names and catalog numbers are valid.**_

While listening through an older recording it happens that you don't remember what it was exactly you played. Just skip over an unknown track and move on with writing down the rest of the mix. When you've later figured out what it was you played, squeeze in tracks at the right position in the mix with:

`dsc search "artist title album" -m my_mix -t A2 -p 12`

The -p option works in combination with the mix subcommands well:

`dsc mix my_mix -a "artist title album" -p 12`

_**Note if you are new to command line tools: Make use of your shells command history and re-use and edit your commands. Usually this is done using cursor keys up and down.**_

More about the subcommands used in this guide is found here: [mix command](MANUAL.md#the-mix-command), [search command](MANUAL.md#the-search-command).



### I'm stuck in a mix

You're in the process of compiling a mix for a gig. You just played this one tune that was really fitting well, but now you're stuck and don't know how to move on. You try out different records, nothing seems to work.

DiscoDOS can tell you in what combinations you ever played this tune in the past:

`dsc suggest "search terms to find the tune"`

Another option would be to let it show you a pool of tracks sharing similiar key and BPM:

`dsc suggest -k Am -b 123`

_**Note: If your tune(s) do not have key and BPM data yet, let them "match" with MusicBrainz first, by using the [update from *Brainz](MANUAL.md#search-action-update-from-brainz) search action**_



### I'd like to quickly rate my transitions

You are listening to a recording of a mix you have already documented into DiscoDOS and now would like to quickly rate your transitions, so you and DiscoDOS can learn from it.

Use the bulk-edit function to change specific fields of your mix's tracks:

`dsc mix "the mix name" -b trans_rating,trans_notes`

Learn more about this function in the [mix command section](MANUAL.md#the-mix-command).

_**Note: Currently DiscoDOS rating analysis system is not finished. This will be coming in future version. As a preparations for this feature, you only are allowed to put these character combinations into the trans_rating field: ++, +, ~, -, --**_



### I got a new record and want to quickly use it in DiscoDOS without re-importing everything

Search for the record on discogs.com. Copy the release ID or the whole URL (eg. https://discogs.com/release/123456) and import it:

`dsc import release 123456`

or

`dsc import release https://discogs.com/release/123456`

Get artist/title for each track

`dsc search 123456 -u`

Get key and BPM from MusicBrainz/AcousticBrainz:

`dsc search 123456 -zz`

_**Note: Certainly you can always find a tune in your collection by using search terms. You don't have to use the release ID. We use it here because we have it at hand already**_

A regular search command and starting *Brainz matching:

`dsc search "new release new tune" -zz`

There is another convenient way when you are in the process of writing down a mix, and realize you can't find the release because you didn't add it to the collection yet: Use the -a option of the mix subcommand. Then, instead of searching for a text-term, we hand over a Discogs release ID. DiscoDOS will look for this exact release ID and add it to your Discogs collection as well as to the local DiscoBASE. As expected with the `mix -a` commmand, the interactively selected track will be added to your mix too:

`dsc mix fat_mix -a 123456`



### I'd like to get as much information about my music as possible - in one go!

As you've probably learned already, DiscoDOS doesn't import all information about a record collection at once but rather "on user request". Eg. single tracks or whole mixes can be asked to be filled in with additional data from Discogs or AcousticBrainz. When dealing with record collections containing hundreds or even thousands of records, obviously working through all of them via the APIs of online information services takes a lot of time, but certainly DiscoDOS can be asked to do it:

To make a full import of your whole record collection from Discogs (all releases INCLUDING all tracks on them) execute:

`dsc import tracks`

_**Note: This command can also be used for an initial import (you just started using DiscoDOS - DiscoBASE is still empty).**_

_**1000 records including a total of 3000 tracks complete in about 20 minutes**_

To get additional data from MusicBrainz and AcousticBrainz (key, BPM, weblinks to release- and recordingpages), execute:

`dsc import brainz`

_**Note: This command requires the import-tracks command above, being completed already.**_

_**This process will take hours and hours, depending on the size of your collection**_

Read more on "*Brainz matching and importing" and it's performance in the [the import command chapter](MANUAL.md#the-import-command-group). You will also learn how the process could be resumed if for some reason the computer had to be switched off or the connection broke away.

Here's a trick to execute both commands one after the other. We use the "command concatination" features of our shell:

On Windows, do:

`dsc import tracks  &  dsc import brainz`

on macOS or Linux it's:

`dsc import tracks  &&  dsc import brainz`

Leave this running "overnight" - You will see a final summary after each of the commands completes, telling you the exact time it was running and how much information was processed and imported. If you'd like to help improve this manual, copy/paste your stats into a [Github issue](https://github.com/JOJ0/discodos/issues), it would help me a lot to state more accurate estimates here.



### I'd like to use my DiscoBASE on multiple computers

DiscoDOS includes a built-in backup and restore feature that can also be used to sync a DiscoBASE between multiple computers.

We need a place to store our discobase.db file online. Currently there are two options:
- Dropbox
- A folder on a webserver

This section will describe how to use Dropbox only, find the webserver option documented here: FIXME

To allow DiscoDOS access to your Dropbox account you need an access token. To obtain it follow the steps in chapter [Configure Dropbox Access for _discosync_](INSTALLATION.md#configure-dropbox-access-for-discosync), then come back here.

To backup your DiscoBASE, execute:

`discosync --backup` or in short `discosync -b`

To restore it on another computer, execute:

`discosync --restore` or in short `discosync -r`

_**Note: Certainly you can use this feature to backup and restore your DiscoBASE on one computer only. The commands are the same**_



## User's Manual

Even more details on what DiscoDOS can do is found in the [User's Manual](MANUAL.md). This quickstart guide should have given you a first impression on how things work, now consult the User's Manual for advanced usage concepts. You will also find some background info on how things work and why.
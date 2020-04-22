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

### Installation

Please head over to the [INSTALLATION](https://github.com/JOJ0/discodos/blob/master/INSTALLATION.md) document for step by step instructions on how to get DiscoDOS running on your machine.


### Importing your Discogs collection

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

## Update database from Discogs

You can update your DiscoBASE from your Discogs collection at any time, if data is already existing, it will be updated.

`disco import`

Due to the Discogs API being not the fastest, it quite takes some time though. There are other ways for adding single releases to Discogs AND to your DiscoBASE simultaneously. Check out the command below. First of all notice that we are in "mix mode" and use the -a option to add a release/track to a mix from there. Then, instead of searching for a text-term we hand over a Discogs release ID. DiscoDOS will look for this exact release ID and add it to your Discogs collection as well as to the local DiscoBASE.

`disco mix fat_mix -a 123456`

An alternative, if you are not about to add this new release to a mix and just want to add it to Discogs collection _and_ to the DiscoBASE (to have it available for future mixes) you can use the -a option whith the import subcommand:

`disco import -a 123456`

To add a release to DiscoBASE **only** (because it's been already added to your collection via the Discogs web interface) you just use the import command in the setup script with a release ID attached. (Sidenote: Unfortunately this way it takes significantly longer because of drawbacks in how the API is accessible via the API):

`disco import 123456`
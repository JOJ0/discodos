---
layout: page
---

DiscoDOS is a sophisticated and flexible command line tool that brings
typical features known from digital DJing systems to the Vinyl DJ. Create
playlists, fetch key and BPM, let DiscoDOS help you search your collection.

``` bash
                _______  _______ ________
               /       \        /       /
              /  ___   /  ___  /  _____/
             /  /  /  /  /  /  \____  \
            /  /__/  /  /__/  _____/  /
D i s c o  /                /        /
          /_______/\_______/________/
```

is based on data pulled from a users [Discogs](https://www.discogs.com)
record [collection](https://support.discogs.com/hc/en-us/articles/360007331534-How-Does-The-Collection-Feature-Work-).
Tracks can be organized into playlists and mix-transitions rated.
Additionally the collection can be linked to the online music information
services [MusicBrainz](https://musicbrainz.org) and
[AcousticBrainz](https://acousticbrainz.org) to retrieve further information
about your music (e.g key and BPM).

## Installation
- [Windows Installer](https://github.com/JOJ0/discodos/releases/download/v1.1.0/DiscoDOS-1.1.0-Win.exe)
- [macOS Installer](https://github.com/JOJ0/discodos/releases/download/v1.1.0/DiscoDOS-1.1.0-macOS.dmg)
- Linux - read the [Installation Guide](https://discodos.readthedocs.io/en/latest/INSTALLATION.html#linux)
- Install [the latest development version](https://discodos.readthedocs.io/en/latest/CONTRIBUTION.html)
directly from git master

DiscoDOS guides you through its setup automatically on first run. For further
assistance especially on accessing your personal Discogs record collection,
read [this chapter](https://discodos.readthedocs.io/en/latest/INSTALLATION.html#configure-discogs-api-access)
of the Installation Guide.


## Usage

View the [Quickstart Guide](https://discodos.readthedocs.io/en/latest/QUICKSTART.html).

## Youtube Tutorials


{% include youtube.html id="c9lqKuGSCVk" url_append="" %}
This video presents the concepts of Mixes, Suggestions, Discogs Collection, AcousticBrainz (7 min view)

{% include youtube.html id="agp9OrYC66I" url_append="" %}
Finding key & BPM compatible tracks in your Discogs Collection (1 min view)

{% include youtube.html id="4lungDgdJ2w" url_append="" %}
How to fetch key & BPM from AcousticBrainz (2 min view)


## DiscoDOS is FOSS

DiscoDOS is Free and Open Source Software and licensed under the GNU General Public License (GPL3). If you are a developer or a tech-interested person, check out the [project repository](https://github.com/JOJ0/discodos) on github.


## Roadmap

Well, there is no actual roadmap but just some ideas in what direction this
software could advance and things that I personally would find nice to have.
If you have any preference or ideas yourself, please let me know ([file a
github issue](https://github.com/JOJ0/discodos/issues/new))

Primarily DiscoDOS was built to help me write down and analyze my Vinyl sets
but often I play both Vinyl and Digital. It would be cool if DiscoDOS could
view an internal playlist together with lists from digital DJing software. I
did some research already and think it should be doable without too much
hassle. In order of my personal preference (and supposed ease of
implementation) the DJing systems I am talking about are:

  - NI Traktor
  - Mixxx
  - Pioneer Rekordbox

An alternative approach to finding out musical key and BPM via AcousticBrainz
(which will be discontinued in 2023) is to use the information saved in media
files metadata on the user's harddisk. There is loads of tools existing already
that manage to find out key, BPM and other things and tag files accordingly.
Each track in the DiscoDOS `track` table could be matched with a file in the
user's digital music collection, best by using an awesome tool that is already
existing: [Beets](https://beets.io). The Beets database of a user could be
queried to find out where a specific releases tracks are located on the
harddisk.

Since python3-discogs-client (which DiscoDOS uses to access discogs.com) was
extended to handle a user's sales inventory, I was thinking to build a `disco
sell` command into DiscoDOS.

More color in DiscoDOS would be nice! Colors on terminal are limited and
cross-platform compatibility is probably not easy but still - who doesn't
love colored terminal text?

The *Brainz matching algorithm is working quite well and does find a lot (if
available) but there is room for improvement.

Some people say they prefer GUIs over text consoles? Can you imagine that?
Just kidding, yes a neat GUI version of DiscoDOS would be beneficial to a lot
of people, even myself (duh!). I was thinking of something modern, "web-like"
and would prefer if it would be based on React/Javascript. I even started to
play around with React Native and coded a working draft for iOS and Android
already. A second reason for choosing React also for the Desktop version
would definitely be that on the long run, parts of code could be shared
between desktop and mobile version.

Update 2022: Thoughts regarding GUI:

- I would rather prefer to write a GUI in Googles Flutter than in React Native.
Similar to React Native, Flutter also would be beneficial in terms of reusing
code to write a regular "webapp version" of DiscoDOS.

- A draft of a GUI written in PyQT5 was contributed to DiscoDOS in 2021 and I
continued working on it. Since I'm not a very skilled QT programmer (yet) and
don't find the time, there only is a preview available that is working fine but
misses quite some functionality to really make it useful. See the release notes
of [Discodos 1.1](https://github.com/JOJ0/discodos/releases/tag/v1.1) for
details on how to try it out.

Any other ideas how DiscoDOS could be improved? [Let me
know!](https://github.com/JOJ0/discodos/issues/new)

## Changelog

Find out what changed between DiscoDOS versions on the [github releases
page](https://github.com/JOJ0/discodos/releases)

## Stay up-to-date

DiscoDOS is registered on [libreav.org](https://libreav.org), a site
collecting information about Free and Open Source music software.

- [DiscoDOS on libreav.org](https://libreav.org/software/discodos)

There is an IRC channel that announces whenever new versions are released. Join
#libreav on freenode.net, or if you are registered on matrix.org
or any other Matrix homeserver, join room
[#freenode_#libreav:matrix.org](https://matrix.to/#/#freenode_#libreav:matrix.org).

Alternatively register to the [J0J0 Todos
mailinglist](https://blog.jojotodos.net/mailinglist/)

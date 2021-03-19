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
- [Windows Installer](https://github.com/JOJ0/discodos/releases/download/v1.0.0-rc4/DiscoDOS-1.0.0-rc4-Win.exe)
- [macOS Installer](https://github.com/JOJ0/discodos/releases/download/v1.0.0-rc4/DiscoDOS-1.0.0-rc4-macOS.dmg)
- Linux - read the [Installation Guide](https://discodos.readthedocs.io/en/latest/INSTALLATION.html#linux)

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
github issue](https://github.com/JOJ0/discodos/issues))

Primarily DiscoDOS was built to help me write down and analyze my Vinyl sets
but often I play both Vinyl and Digital. It would be cool if DiscoDOS could
view an internal playlist together with lists from digital DJing software. I
did some research already and think it should be doable without too much
hassle. In order of my personal preference (and ease of implementation) the
DJing systems I am talking about are:

  - NI Traktor
  - Mixxx
  - Pioneer Rekordbox

Recently someone added a feature to handle a user's sales inventory with
python3-discogs-client (which DiscoDOS uses to access discogs.com). I was
thinking to build a `disco sell` command into DiscoDOS.

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

Any other ideas how DiscoDOS could be improved? [Let me
know!](https://github.com/JOJ0/discodos/issues)

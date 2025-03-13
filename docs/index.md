---
layout: page
---

{% include_relative discodos_readme.md %}

## Screenshots

The DiscoDOS documentation has a dedicated section featuring [screenshots, animated Gifs and videos](https://discodos.readthedocs.io/en/latest/VIDEO_TUTORIALS.html).

## History

At first, back in 2018, I wrote DiscoDOS to replace my pencil and paper notes on mixes I played. In 2020 version [1.0](https://github.com/JOJ0/discodos/releases/tag/v1.0_rc2) was finished and I use it ever since. In early 2023 I re-wrote the command line interface to use [Click](https://click.palletsprojects.com/en/stable/why/) instead of Python's built-in `argparser` (version [2.0](https://github.com/JOJ0/discodos/releases/tag/v2.0)). In late 2024 I implemented features around selling records on the Discogs Marketplace and better handling collection items including support for the _custom folder features_ Discogs provides (versions [3.0](https://github.com/JOJ0/discodos/releases/tag/v3.0) and [3.1](https://github.com/JOJ0/discodos/releases/tag/v3.1)).

## Roadmap-ish

Well, there is no actual roadmap but a list of ideas in what direction DiscoDOS could advance and things that I personally would find nice to have.

If you have any preference or ideas yourself, please let me know by [opening a GitHub issue](https://github.com/JOJ0/discodos/issues/new).

- [x] In its first versions DiscoDOS was built to write down and analyze Vinyl sets.
- [ ] It would be cool if DiscoDOS could view an internal playlist together with lists from digital DJing software, eg. [Mixxx](https://mixxx.org) and [Pioneer Rekordbox](https://rekordbox.com)
- [ ] That idea could also be solved by integrating with a music library management software like [Beets](https://beets.io).
- [ ] An alternative approach to finding out musical key and BPM via AcousticBrainz (which was discontinued in 2023) could be to use the information saved in media files metadata on the user's harddisk. There is loads of tools existing already that manage to find out key, BPM and other things and tag files accordingly. Each track in the DiscoDOS `track` table could be matched with a file in the user's digital music collection, best by using an awesome tool that is already existing: [Beets](https://beets.io). The Beets database of a user could be queried to find out where a specific releases tracks are located on the harddisk.
- [x] Since python3-discogs-client (which DiscoDOS uses to access discogs.com) was extended to handle a user's sales inventory, I was thinking to build a `dsc sell` command into DiscoDOS allowing to list new records for sale and a way to comfortably edit those listing later (This became the `dsc ls` TUI interface).
- [x] More color in DiscoDOS would be nice! Colors on terminal are limited and
cross-platform compatibility is probably not easy but still - who doesn't
love colored terminal text?
- [x] A neat GUI version of DiscoDOS would be beneficial. First ideas were something React Native or Flutter based (mobile and web friendly). Along the way there were some approaches by contributors written in Tkinter and PyQT that were never finished though. In 2024/2025 this idea evolved into at least write some parts in a GUI-ish way. The `dsc ls` command based on the [Textual](https://textual.textualize.com) framework is quite feature-rich by now.

## Changelog

Find out what changed between versions on the [DiscoDOS releases page](https://github.com/JOJ0/discodos/releases)

## Stay up-to-date

DiscoDOS is registered on [libreav.org](https://libreav.org/software/discodos), a site collecting information about Free and Open Source music software (which seems to be broken or discontinued by now - in 2025).

There is an IRC channel that announces whenever new versions are released. Join #libreav on freenode.net, or if you are registered on matrix.org or any other Matrix homeserver, join room [#freenode_#libreav:matrix.org](https://matrix.to/#/#freenode_#libreav:matrix.org).

Register to the [J0J0 Todos mailinglist](https://blog.jojotodos.net/mailinglist/)

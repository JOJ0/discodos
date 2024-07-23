<!-- omit in toc -->
# Installation Guide

- [Install released version](#install-released-version)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Configure Discogs API access](#configure-discogs-api-access)
  - [Edit configuration file manually](#edit-configuration-file-manually)
- [Configure _discosync_ - The DiscoDOS backup & sync tool](#configure-discosync---the-discodos-backup--sync-tool)
  - [Configure Dropbox Access for _discosync_](#configure-dropbox-access-for-discosync)
  - [Configure a webserver folder for _discosync_](#configure-a-webserver-folder-for-discosync)


There are two ways of installing DiscoDOS:

- Released version (get a program that just works, is easy to install and well tested)
- Development version (get the latest features, contribute to DiscoDOS by trying out new things and reporting back what you think. There is a separate document about [installing the development version](CONTRIBUTION.md).


## Install released version

### Windows

Download the latest Windows installer (`DiscoDOS_version.exe`) from the [release page](https://github.com/JOJ0/discodos/releases) and run it.

Click Start Menu - DiscoDOS - DiscoDOS

A new command prompt window opens and the DiscoDOS main command `dsc` runs automatically.

On first launch, `dsc` will create a configuration file for you. To access your Discogs collection, an access token has to be generated and put into the file. Follow the steps in chapter [Configure Discogs API access](#configure-discogs-api-access), then come back here!


Now that you've put the token into the configuration file, DiscoDOS completes setup by creating a local database (the DiscoBASE).

**Note: In case you are updating from a previous DiscoDOS version, your data will be kept and your database's schema might be upgraded automatically**

If the connection to Discogs is working, setup asks you to view a little tutorial teaching you how it works - hit enter and follow the steps.

Your starting point for further documentation is the [Quickstart Guide](QUICKSTART.md#importing-your-discogs-collection). Your next logical step is importing your Discogs collection.

**Note: The `dsc` and `discosync` commands are installed globally, you can use the Start Menu entry to run them but they also work in any cmd.exe window.**


**Note: DiscoDOS generates the following files which are kept in `C:\Users\your_name\Documents\discodos\` (path may vary depending on your OS-language):**

 - The DiscoDOS configuration file (`config.yaml`)
 - The DiscoBASE (`discobase.db`)
 - A logfile (`debug.log`)

#### Improve Command Line Experience on Windows

I would highly recommend installing "Microsoft Windows Terminal". It will provide a much nicer command line experience than cmd.exe! It has a better looking font out of the box, better command auto completion and overall is the command line application Windows was missing for ages (IMHO). Future DiscoDOS versions will use Windows Terminal in the Start Menu launchers by default.

##### Get "Microsoft Windows Terminal"
 - from the Microsoft App store (you'll find it in your Start Menu and you need a Microsoft account)
   - get a stable release version
 - or from the Microsoft github page: https://github.com/microsoft/terminal/releases
   - get a stable release version
   - or one of the preview version (I'd recommend them, they are usually stable enough!)

##### Some features worth trying out
  - Zoom in/out (resize terminal text) using "ctrl + mouse wheel" (e.g handy when showing mixes in verbose view (`dsc mix mix_name -v`)
    - Alternatively zoom in/out using "ctrl +/ctrl -"
  - Paste text from clipboard using "right/secondary mouse button"
  - Command completion using "tab key" (cmd.exe had this already, yes - anyway it feels a little better here IMHO)
  - Open a new terminal windows using "ctrl - shift - n"
  - Open a new terminal tab using "ctrl - shift - t"


### macOS

Download the latest macOS package (`DiscoDOS_version.dmg`) from the [release page](https://github.com/JOJ0/discodos/releases)


Doubleclick the .dmg file - Drag and drop `DiscoDOS.app` to `Applications` folder. 

Launch DiscoDOS.app

A new Terminal window opens and the DiscoDOS main command `dsc` runs automatically.

On first launch, `dsc` will create a configuration file for you. To access your Discogs collection, an access token has to be generated and put into the file. Follow the steps in chapter [Configure Discogs API access](#configure-discogs-api-access), then come back here!

Now that you've put the token into the configuration file, DiscoDOS completes setup by creating a local database (the DiscoBASE).

**Note: In case you are updating from a previous DiscoDOS version, your data will be kept and your database's schema might be upgraded automatically**

If the connection to Discogs is working, setup asks you to view a little tutorial teaching you how it works - hit enter and follow the steps.

Your starting point for further documentation is the [Quickstart Guuide](QUICKSTART.md#importing-your-discogs-collection). Your next logical step is importing your Discogs collection.

**Note: The `dsc` and `discosync` commands are now installed globally, you can launch DiscoDOS.app to open a Terminal but they also work in any other Terminal window.**

**Note: DiscoDOS generates the following files which are kept in `/Users/your_name/Documents/DiscoDOS/`:**

 - The DiscoDOS configuration file (`config.yaml`)
 - The DiscoBASE (`discobase.db`)
 - A logfile (`debug.log`)


### Linux

Most Linux distributions come with a compatible Python3 version in there package repositories already. Please refer to the [contribution manual](CONTRIBUTION.md#macos-or-linux---install-system-wide) on how to install the DiscoDOS Python package.

~~If you use Debian GNU/Linux or any distribution that is based on it: DiscoDOS v1.0_rc2 is available in Debian unstable. It is also available in the current Ubuntu release as well as in Ubuntu Studio, Linux Mint and other Ubuntu-based distros. Just `apt install discodos` and you are good to go. If you'd like to use the latest version of DiscoDOS please be patient or even better: Install DiscoDOS as a Python package. Learn how by following above link to the contribution manual.~~

_Note: The DiscoDOS package for Debian is no longer maintained. If you think that's a shame or would welcome any other form of (Linux-)packaging, please [drop me a line](https://github.com/JOJ0/discodos/issues) and let's discuss it._

## Configure Discogs API access

To access your Discogs collection you need to generate an API login token and put it into the configuration file.

- Login to discogs.com
- Click your avatar (top right)
- Select _Settings_
- Switch to section _Developers_
- Click _Generate new token_
- Run `dsc` - you'll be prompted to put in the token.

**Note: If you are updating from a previous DiscoDOS version, your config.yaml is existing and has a token set up already, thus you won't be bothered!**

- Jump back to [Windows installation chapter](#windows)
- Jump back to [macOS installation chapter](#macos)
- Jump back to [Linux installation chapter](#linux)

### Edit configuration file manually

Alternatively you can open the configuration file with a texteditor and copy/paste the generated Discogs token into it by hand:
- _Windows_: Edit `MyDocuments/discodos/config.yaml`
  (use Start Menu entry "DiscoDOS/Edit Configuration File")
- _macOS_: Edit `/Users/your_name/Documents/config.yaml` (secondary click (two fingers) - "Open With" - "TextEdit.app").
- _Linux_: Edit `$HOME/.discodos/config.yaml`

The line in `config.yaml` should look something like this then:

 ```
 discogs_token: XDsktuOMNkOPxvNjerzCbvJIFhaWYwmdGPwnaySH
 ```




## Configure _discosync_ - The DiscoDOS backup & sync tool

`discosync` works with timestamps (local modification time) of the database file. It will never backup a file that has been already backuped up. Even if the file has been shared to another computer, it will only be overwritten if its contents was changed. This is to reduce the amount of (useless) backup files in your dropbox account or on your webserver.

The format of files always is "database_name_YYYY-MM-DD_HHMMSS.db"


### Configure Dropbox Access for _discosync_

To prepare your Dropbox account and DiscoDOS configuration, do the following:

- We need to create a new "Dropbbox App" in your account: https://www.dropbox.com/developers/apps/create
- Step 1: "Choose an API" - select "Dropbox API"
- Step 2: "Choose the type of access you need" - select "App folder"
- Step 3: "Name your app" - enter "discodos"
- Click "Create app"
- Scroll down to section "OAuth 2" - Click the "Generate" button right below "Generated access token"
- Double click and copy the token to the clipboard
- Put the token into the config.yaml file on all the computers you would like to use this DiscoBASE.
  - open with TextEdit.app on Mac
  - open with Notepad on Windows.

The line in config.yaml should then look something like this (watch out for the surrounding quotes):

```
dropbox_token: 'abcxyzabcxyzabcxyzabcxyzabcxyzabcxyzabcxyz'
```

- Jump back to [I'd like to use my DiscoBASE on multiple computers](QUICKSTART.md#id-like-to-use-my-discobase-on-multiple-computers)

If you want to delete your Dropbox app again or generate a new token because you lost it, go to the [Dropbox app console](https://www.dropbox.com/developers/apps?_tk=pilot_lp&_ad=topbar4&_camp=myapps).

Certainly you can also access the backup files via the Dropbox webinterface - Click the "discodos" app on the home screen - you will find a subfolder "discodos" containing all your backed up DiscoBASE files.


### Configure a webserver folder for _discosync_

If you don't like saving your stuff to Dropbox and happen to have your own personal webspace somewhere, `discosync` can use it to save backups. The folder needs to have these features enabled:

- [WebDAV](https://en.wikipedia.org/wiki/WebDAV)
- Password restriction ([HTTP Basic Access Authentication](https://en.wikipedia.org/wiki/Basic_access_authentication))

Even though it is not mandatory, the following is highly recommended to securly transport your password over the wire:

- Webserver running SSL (https://...)

Configuration steps may vary, if you can't do above configurations in your webhosters "configuration console" try contacting their support.

If you have (root) access to your server and it's an Apache webserver, configuration of a suitable folder looks like this:

```
   <Directory /var/www/discodos/>
      AllowOverride None
      DAV On
      AuthType "Basic"
      AuthName "Restricted Area"
      AuthBasicProvider file
      AuthUserFile "/etc/apache2/.htaccess_discodos"
      Require user my_discosync_user
   </Directory>
```

To create the password file:

```
htpasswd -c /etc/apache2/.htaccess_discodos my_discosync_user
```

Test if accessing your backup space is working with your webbrowser: https://www.yourdomain.com/discodos/. Usually a popup asks you for your credentials.

If everything's fine adjust your DiscoDOS configuration file (`config.yaml`)

```
webdav_user: 'my_discosync_user'
webdav_password: 'secret123'
webdav_url: 'https://www.yourdomain.com/discodos/'
```

Go to the [discosync chapter in the User's manual](MANUAL.md#discosync---the-discodos-backup--sync-tool)
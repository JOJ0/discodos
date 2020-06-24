<!-- omit in toc -->
# DiscoDOS Installation

- [Install released version](#install-released-version)
  - [Windows](#windows)
  - [macOS/Linux](#macoslinux)
- [Configure Discogs API access](#configure-discogs-api-access)
- [Configure _discosync_ - The DiscoDOS backup & sync tool](#configure-discosync---the-discodos-backup--sync-tool)
  - [Configure Dropbox Access for _discosync_](#configure-dropbox-access-for-discosync)
  - [Configure a webserver folder for _discosync_](#configure-a-webserver-folder-for-discosync)


There are two ways of installing DiscoDOS:

- Released version (get a program that just works, is easy to install and well tested)
- Development version (get the latest features, contribute to DiscoDOS by trying out new things and reporting back what you think. There is a separate document about [installing the development version](https://github.com/JOJ0/discodos/blob/master/CONTRIBUTION.md).


## Install released version

basically the steps on every OS are similar:

* download package
* unpack
* launch DiscoDOS' main command `disco`
  * a local database will be initialized (the DiscoBASE)
  * the DiscoDOS CLI tools will be set up for your user environment
* configure Discogs API access


### Windows

download the latest Windows package from the [release page](https://github.com/JOJ0/discodos/releases)

unpack - it contains a folder named `discodos`.

You can move the `discodos` folder whereever you like inside your user profile. If unsure or not too familiar with command line tools I suggest you just put it directly into your users "home folder" (`c:\Users\your_name\discodos`).

Start a command prompt window (start button - type `cmd` - enter). Change into the discodos folder and see what's in there:

```
cd discodos
dir
```

You should see 3 files: `disco.exe`, `discosync.exe` and `config.yaml`

Launch DiscoDOS' main command:

`disco`

A local **database** (the so-called DiscoBASE) and an additional file (`discoshell.bat`) was just created in your discodos folder.

Configure access to your Discogs collection as described in chapter [Configure Discogs API access](#configure-discogs-api-access), then come back here!

Start using DiscoDOS by double clicking the newly created batch file `discoshell.bat` - make a shortcut to it on your Desktop.

Launch the `disco` command again (inside your DiscoSHELL window) - if the connection to Discogs is working it will ask you to view a little tutorial teaching you how it works - hit enter and follow the steps.

Your starting point for further documentation is the [README page](https://github.com/JOJ0/discodos/blob/master/README.md#importing-your-discogs-collection). Your next step will be to import your Discogs collection.


### macOS/Linux

download the latest macOS or Linux package from the
[release page](https://github.com/JOJ0/discodos/releases)

unpack - on a Mac just double click the tar.gz file, it will extract a folder named `discodos`. On Linux do something like this:

```
tar xvzf discodos-1.0-rc1-macOS.tar.gz
ls -l discodos
```

You can move the `discodos` folder whereever you like inside your user profile. If unsure or not too familiar with command line tools I suggest you just put it directly into your users "home folder" (on a Mac: `/Users/your_name/discodos`).

Assuming your discodos folder resides directly in your home folder, start a terminal, if you haven't already (on Mac: Applications - Utilities - Terminal.app). Jump right into the discodos folder and see what's in there:

```
cd discodos
ls -l
```

You should see 3 files: `disco`, `discosync` and `config.yaml`

Launch DiscoDOS' main command:

`./disco`

A local **database** (the so-called DiscoBASE) and an additional file (`install_wrappers_to_path.sh`) was just created in your discodos folder.

To make `disco` easily launchable without having to type `./` in front of it, execute this script once:

`./install_wrappers_to_path.sh`

Configure access to your Discogs collection as described in chapter [Configure Discogs API access](#configure-discogs-api-access), then come back here!

Launch the `disco` command again - if the connection to Discogs is working it will ask you to view a little tutorial teaching you how it works - hit enter and follow the steps.

Your starting point for further documentation is the [README page](https://github.com/JOJ0/discodos/blob/master/README.md#importing-your-discogs-collection). Your next step will be to import your Discogs collection.


## Configure Discogs API access

To access your Discogs collection you need to generate an API login token and put it into the configuration file.

- Login to discogs.com
- Click your avatar (top right)
- Select _Settings_
- Switch to section _Developers_
- Click _Generate new token_
- Open the file `config.yaml` (inside the discodos root folder, next to the files `setup.py` and `cli.py`) and copy/paste the generated Discogs token into it:
  - on Windows right click the file - select "Open With" - choose "Notepad" - paste token to the right place (as shown below).
  - on Mac secondary click/tab (two fingers) - select "Open With" - chooose "TextEdit.app" - paste token to the right place (as shown below).

The line in config.yaml should look something like this then (watch out for the surrounding quotes):

 ```
 discogs_token: 'XDsktuOMNkOPxvNjerzCbvJIFhaWYwmdGPwnaySH'
 ```

- Save and close the file
- Jump back to [Windows installation chapter](#windows)
- Jump back to [macOS/Linux installation chapter](#macoslinux)



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

- Jump back to [I'd like to use my DiscoBASE on multiple computers](README.md#id-like-to-use-my-discobase-on-multiple-computers)

If you want to delete your Dropbox app again or generate a new token because you lost it, go to the [Dropbox app console](https://www.dropbox.com/developers/apps?_tk=pilot_lp&_ad=topbar4&_camp=myapps).

Certainly you can also access the backup files via the Dropbox webinterface - Click the "discodos" app on the home screen - you will find a subfolder "discodos" containing all your backed up DiscoBASE files.


### Configure a webserver folder for _discosync_

If you don't like saving your stuff to Dropbox and happen to have your own personal webspace somewhere, `discosync` can use it to save backups. The folder needs to have these features enabled:

- [WebDAV](#https://en.wikipedia.org/wiki/WebDAV)
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

Go to the [discosync chapter in the User's manual](MANUAL.md#discosync-the-discodo-backup---sync-tool)
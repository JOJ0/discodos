<!-- omit in toc -->
# Setup

## Prerequisites

You need to have these software packages installed
* git
* Python version 3.9 or higher

Getting them differs according to your OS

* Most Linux distributions have git and Python available within their package repositories.
* On Windows download from here: https://git-scm.com/download, https://www.python.org/downloads
* On MacOS I suggest getting both packages via homebrew: https://brew.sh/
  (If homebrew seems overkill to you, just use the Windows links above)

Make sure git and python can be executed from everywhere (adjust your PATH environment variable accordingly).

During the Python setup on Windows choose "Customize installation" and select the following options:

- pip
- py launcher
- Associate files with Python (requires the py launcher)
- Add Python to environment variables


## Windows

Please use the regular command prompt window (cmd.exe) and not the "git bash", otherwise the statements using the %HOMEPATH% environment variable won't work! Also note that Windows paths can be written with slashes instead of the usual backslashes these days (putting them inside of quotes is mandatory though!) - in the very unlikely case your Windows version doesn't support this, please just change the paths to use backslashes.

Create and activate a virtual Python environment!

```
python -m venv "%HOMEPATH%/python-envs/discodos"
"%HOMEPATH%/python-envs/discodos/Scripts/activate.bat"
```

Double check if your environment is active and you are using the pip binary installed _inside_ your %HOMEPATH%/python-envs/discodos directory.

`pip --version`

Install DiscoDOS and its dependencies into your environment:

`pip install discodos`

Launch DiscoDOS' main command and follow the steps shown:

`dsc`

_**Note: Make sure you always first activate your virtual environment when coming back to developing or using DiscoDOS:**_

`"%HOMEPATH%/python-envs/discodos/Scripts/activate.bat"`


## macOS or Linux

### Create a virtual environment

Create and activate a virtual Python environment! The environment will be saved inside a hidden subfolder of your homedirectory called .venvs/

```
python3 -m venv ~/.venvs/discodos
source ~/.venvs/discodos/bin/activate
```

Double check if your environment is active and you are using the pip binary installed _inside_ your ~/.venvs/discodos/ directory.

`pip --version`

### Install a released package from PyPI

Install DiscoDOS and its dependencies into your environment:

`pip install discodos`

### Install latest development version from Git

Jump to your homedirectory, clone the repo and change into the cloned repo directory.

```
cd
git clone https://github.com/JOJ0/discodos.git
cd discodos
```

Install DiscoDOS and its dependencies into your environment:

`pip install -e .`

### Verify installation

Some command wrappers should have been installed too. Verify if they exist inside your `~/.venvs/discodos/bin` directory:

```
which dsc
which discosync
```

Launch DiscoDOS' main command and follow the steps shown:

`dsc`

_**Note: Make sure you always first activate your virtual environment when coming back to developing or using DiscoDOS:**_

`source ~/.venvs/discodos/bin/activate`


## macOS or Linux - Install to user environment

This chapter describes how to install the DiscoDOS package into your user's Python environment which is better suitable for just _using_ it, rather than _contributing/developing_.

**_Installing like this is not recommended and might mess up your system's Python installation**_

Install Python 3. On Debian based distros (Ubuntu, Linux Mint, ...), do something like this:

`apt install python3`

on RedHat based (Fedora, CentOS, ...):

`yum install python3`

Install DiscoDOS into your user's Python environment:

`pip install discodos`

### Verify installation

Some command wrappers should have been installed. Verify if they exist:

```
which dsc
which discosync
```

If `which` didn't find those commands, make sure your $PATH environment variable contains the path the wrappers where installed to. Usually this is `~/.local/bin/`

_Note: On Debian-based systems there might be a file `/usr/bin/dsc` on your system already provided by package mono-devel, thus depending on the order of paths in `$PATH`, `/usr/bin/dsc` might be found before the DiscoDOS wrapper. Change `$PATH` to first search in `~/.local/bin` (export it in `.zshrc`, `.bashrc` or whatever shell you are using)_

Launch DiscoDOS' main command:

`dsc`


## Initial configuration and additional notes

On first launch, `dsc` will create a configuration file for you. To access your Discogs collection, an access token has to be generated and put into the file. Follow the steps in chapter [Configure Discogs API access](INSTALLATION.md#configure-discogs-api-access), then come back here!

Now that you've put the token into the configuration file, DiscoDOS completes setup by creating a local database (the DiscoBASE).

**Note: In case you are updating from a previous DiscoDOS version, your data will be kept and your database's schema might be upgraded automatically**

Your starting point for further documentation is the [Quickstart Guide](QUICKSTART.md#importing-your-discogs-collection-and-marketplace-inventory). Your next logical step is importing your Discogs collection.

**Note: DiscoDOS generates the following files which are kept in `~/.discodos/`:**

 - The DiscoDOS configuration file (`config.yaml`)
 - The DiscoBASE (`discobase.db`)
 - A logfile (`debug.log`)




## Configure Discogs API access

To access your Discogs collection you need to generate an API login token and put it into the configuration file.

- Login to discogs.com
- Click your avatar (top right)
- Select _Settings_
- Switch to section _Developers_
- Click _Generate new token_
- Run `dsc` - you'll be prompted to put in the token.

**Note: If you are updating from a previous DiscoDOS version, your config.yaml is existing and has a token set up already, thus you won't be bothered!**


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
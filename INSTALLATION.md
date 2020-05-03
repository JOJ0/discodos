# DiscoDOS Installation

There are two ways of installing DiscoDOS:

- Release version (get a program that just works, is easy to install and well tested)
- Development version (get the latest features, contribute to DiscoDOS by trying out new things and reporting back what you think. I usually try to keep things stable in the master branch. I use it myself on my production database, so it just has to work. Seldomely there will be major bugs that really could corrupt your data. In any case make sure you use DiscoDOS' neet built-in backup/sync feature!). There is a separate document about [installing the dev-version](https://github.com/JOJ0/discodos/blob/master/CONTRIBUTION.md).


## Install a release version

basically the steps on every OS are similar:

* download package
* unpack
* launch DiscoDOS setup - a config file will be created
* configure Discogs API access
* launch DiscoDOS setup again
  * a local database will be initialized (the DiscoBASE)
  * DiscoDOS CLI tools will be set up for your user environment


### Windows

download the latest Windows package from the
[release page](https://github.com/JOJ0/discodos/releases)

unpack - it contains a folder named `discodos`.

You can move the `discodos` folder whereever you like on your sytem. If unsure or not too familiar with command line tools I suggest you just put it directly into your users "home" (`c:\Users\your_name\discodos`). It sometimes is assumed to be at this place in the DiscoDOS documentation and it's easy to navigate into it: Fire up cmd.exe - you are in your home - cd into discodos folder.

Assuming your discodos folder resides directly in your home folder - start a command prompt window (start button - cmd.exe - enter). Change into the discodos folder and see what's in there:

```
cd discodos
dir
```

You should see 4 files: `cli.exe`, `winconfig.exe`, `sync.exe` and `config.yaml`

Configure access to your Discogs collection as described in chapter [Configure Discogs API Access](#configure-discogs-api-access)

Launch DiscoDOS setup - a local database will be created for you and the command line tools created:

`winconfig`

Start using DiscoDOS by double clicking the newly created batch file `discoshell.bat` - make a shortcut to it on your Desktop.

If you have any troubles or questions arise, please read chapter [DiscoDOS Setup - Troubleshooting](#discodos-setup---troubleshooting), it is an in-detail explanation of what the DiscoDOS setup script does and what differences there are between operating systems.

Launch the `disco` command - if the connection to your Discogs collection is working it will ask you to launch a little tutorial teaching you how it works - answer the question with "y" and follow the steps.

Your starting point for further documentation is the [README](https://github.com/JOJ0/discodos/blob/master/README.md#importing-your-discogs-collection) page.


### macOS/Linux

download the latest macOS or Linux package from the
[release page](https://github.com/JOJ0/discodos/releases)

unpack - on a Mac just double click the tar.gz file, it will extract a folder named `discodos`. If you would like to do it on the terminal, do something like this:

```
cd Downloads
ls -l discodos*
tar xvzf discodos-1.0-rc1-macOS.tar.gz
ls -l discodos
```

You can move the `discodos` folder whereever you like on your sytem. If unsure or not too familiar with command line tools I suggest you just put it directly into your users "home" (on a Mac: `/Users/your_name/discodos`). It sometimes is assumed to be at this place in the DiscoDOS documentation and it's easy to navigate into it: Fire up terminal app - you are in your home - cd into discodos folder.

If you'd like to quickly move it using the terminal, do something like this (assuming you are still in your `Downloads` folder - see commands above). Then also change right into the discodos dir to get started:

```
mv discodos ~/
cd
cd discodos
ls -l
```

You should see 3 files: `cli`, `setup`, `sync` and `config.yaml`

Configure access to your Discogs collection as described in chapter [Configure Discogs API Access](#configure-discogs-api-access)

Launch DiscoDOS setup - a local database will be created for you and the command line tools created:

`./setup`

As a last step, execute the following provided script to customize the CLI tools for your user environment:

`./install_wrappers_to_path.sh`

If you have any troubles or questions arise, please read chapter [DiscoDOS Setup - Troubleshooting](#discodos-setup---troubleshooting), it is an in-detail explanation of what the DiscoDOS setup script does and what differences there are between operating systems.

If everything seems fine, launch the `disco` command - if the connection to your Discogs collection is working it will ask you to launch a little tutorial teaching you how it works - answer the question with "y" and follow the steps.

Your starting point for further documentation is the [README](https://github.com/JOJ0/discodos/blob/master/README.md#importing-your-discogs-collection) page.



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

## DiscoDOS Setup - Troubleshooting

If you have followed the installation steps in above chapters already, you don't have to read through this chapter. It points out what exactly the DiscoDOS setup script does and explains operating system differences. If you had any troubles with above installation steps, it makes sense your read through here though.

_**Make sure you are in DiscoDOS' root folder (usually: `your_homefolder/discodos`)**_

Launch setup and carefully read the output (add .py if installing development version).

`./setup`

Hints if you are about to set up the development version:

* double check the setup command - it's slightly different: `./setup.py`
* Make sure the Python environment you created in the [Development version installation instructions](#development-version) is activated.
* On Windows make sure you have the "py launcher" installed and .py files associated (see setup notes above).
* Also on Windows it could happen that *py launcher* is not properly installed - Work around this issue by launching setup.py with python.exe:
  `python setup.py`

On **first launch** the setup script just creates a config file for you named `config.yaml (release versions have `config.yaml` included already in the package, so this step doesn't apply and step two below immediatly happens!`)

On **second launch** it does several things:

- it creates an empty database -> you should find a file named `discobase.db` in your discodos folder.
- it sets up the DiscoDOS CLI commands
  - Linux/MacOS -> files `disco` `discosetup`, `discosync` and `install_wrappers_to_path.sh` in your discodos folder.
  - Windows -> files `disco.bat`, `discosetup.bat`, `discosync.bat` and `discoshell.bat`
- a configuration file will be created -> `config.yaml`

_**If setup ran through you can try launching `disco` for the first time :-)**_

On **Windows** your starting point always is double-clicking `discoshell.bat` first. A new command prompt window named "DiscoDOS shell" is opened and the "Virtual Python Environment", DiscoDOS needs to function, is activated. Once inside the shell, execute CLI commands via the `disco.bat` wrapper. As usual on Windows systems you can leave out the `.bat` ending and just type `disco`.

On **Linux and MacOS** the workflow is slightly different: To execute DiscoDOS commands, fire up your favorite terminal application and just type `./disco`. (Note if using the development version: This wrapper script also takes care of activating the "Virtual Python Environment"). To conveniently use the `disco` command from everywhere on your system, execute the provided script `./install_wrappers_to_path.sh`

_The following commands assume that, depending on your OS, you are either inside the DiscoDOS shell window or `disco` is being found via the PATH variable (because you've launched `installed_wrappers_to_path.sh` already)._

 Check if the database is working by creating a new mix:

`disco mix my_mix -c`

View your (empty) mix.

`disco mix my_mix`

There is two more commands you should be able to run by now:

* `discosetup` - this is just a wrapper to the setup script you just executed above, you will use it seldomly, it's used for future DiscoDOS updates and fixing things.
* `discosync` - this is the DiscoDOS backup script - you can also use it to sync the database file between different computers (either via dropbox or a webdav enabled folder on a webserver)






# DiscoDOS Installation

There are two ways of installing DiscoDOS:

- Release version (get a program that just works, is easy to install and well tested)
- Development version (get the latest features, contribute to DiscoDOS by trying out new things and reporting back what you think. I usually try to keep things stable in the master branch. I use it myself on my production database, so it just has to work. Seldomely there will be major bugs that really could corrupt your data. In any case make sure you use DiscoDOS' neet built-in backup/sync feature!)


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

You should see 3 files: `cli.exe`, `winconfig.exe` and `sync.exe`

Launch DiscoDOS setup (winconfig.exe) - carefully read the output - a file named config.yaml should have been created for you:

```
winconfig
dir
```

Configure access to your Discogs collection as described in chapter [Configure Discogs API Access](#configure-discogs-api-access)

Launch DiscoDOS setup again - a local database will be created for you and the command line tools created:

`./winconfig`

Start using DiscoDOS by double clicking the newly created batch file `discoshell.bat` - make a shortcut to it on your Desktop.

If you have any troubles or questions arise, please read chapter [Initialize the database and set up the CLI tools](#initialize-the-database-and-set-up-the-cli-tools), it is an in-detail explanation of what the DiscoDOS setup script does and what differences there are between operating systems.

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

You should see 3 files: `cli`, `setup` and `sync`

Launch setup - carefully read the output - a file named config.yaml should have been created for you:

```
./setup
ls -l
```

Configure access to your Discogs collection as described in chapter [Configure Discogs API Access](#configure-discogs-api-access)

Launch setup again - a local database will be created for you and the command line tools created:

`./setup`

As a last step, execute the following provided script to customize the CLI tools for your user environment:

`./install_wrappers_to_path.sh`

If you have any troubles or questions arise, please read chapter [Initialize the database and set up the CLI tools](#initialize-the-database-and-set-up-the-cli-tools), it is an in-detail explanation of what the DiscoDOS setup script does and what differences there are between operating systems.

If everything seems fine, launch the `disco` command - if the connection to your Discogs collection is working it will ask you to launch a little tutorial teaching you how it works - answer the question with "y" and follow the steps.

Your starting point for further documentation is the [README](https://github.com/JOJ0/discodos/blob/master/README.md#importing-your-discogs-collection) page.


## Initialize the database and set up the CLI tools

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

On first launch the setup script just creates a config file for you named `config.yaml`

On second launch it does several things:

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

To finally really make DiscoDOS useful continue with the (final) setup chapter below.


## Configure Discogs API access

To access your Discogs collection you need to generate an API login token and put it into the configuration file.

- Login to discogs.com
- Click your avatar (top right)
- Select _Settings_
- Switch to section _Developers_
- Click _Generate new token_
- Open the file `config.yaml` (inside the discodos root folder, next to the files `setup.py` and `cli.py`) and copy/paste the generated Discogs token into it:

 ```
 discogs_token: 'XDsktuOMNkOPxvNjerzCbvJIFhaWYwmdGPwnaySH'
 ```

- Save and close the file

If you've made it through here, [start using DiscoDOS](https://github.com/JOJ0/discodos/blob/master/README.md#importing-your-discogs-collection)


## Install a development version

DiscoDOS is written entirely in Python. The majority of time, it was coded on a MacOS X 10.13 machine with Python installed via homebrew, thus it's tested well on this platform. There are some users happily using it on Winodws 10 already. I myself also regularily use it on Linux machines too, and it seems to work as good as on my Mac.

Basically it will run on any OS as long as the following prerequisites are met. Please report back in any case, wether it's working fine or you find things that seem unusual on your OS. Thanks a lot!


### Prerequisites

You need to have these software packages installed
* git
* Python version 3.7 or higher

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


### Windows

_Skip this chapter if you are on macOS or Linux!_

Please use the regular command prompt window (cmd.exe) and not the "git bash", otherwise the statements using the %HOMEPATH% environment variable won't work! Also note that Windows paths can be written with slashes instead of the usual backslashes these days (putting them inside of quotes is mandatory though!) - in the very unlikely case your Windows version doesn't support this, please just change the paths to use backslashes.

Jump to your homedirectory, clone the repo and change into the cloned repo directory.

```
cd %HOMEPATH%
git clone https://github.com/JOJ0/discodos.git
cd discodos
```

Create and activate a virtual Python environment!

```
python -m venv "%HOMEPATH%/python-envs/discodos"
"%HOMEPATH%/python-envs/discodos/Scripts/activate.bat"
```

Double check if your environment is active and you are using the pip binary installed _inside_ your %HOMEPATH%/python-envs/discodos directory.

`pip --version`

You should see something like this:

`pip 19.2.3 from c:\users\user\python-envs\discodos\lib\site-packages\pip (python 3.8)`

Install the necessary dependencies into your environment!

`pip install -r "%HOMEPATH%/discodos/requirements.txt"`

Now [initialize the database and set up the CLI tools](#initialize-the-database-and-set-up-the-cli-tools), then [configure Discogs API access](#configure-discogs-api-access)


### Linux / MacOS

Jump to your homedirectory, clone the repo and change into the cloned repo directory.

```
cd
git clone https://github.com/JOJ0/discodos.git
cd discodos
```

Create and activate a virtual Python environment! The environment will be saved inside a hidden subfolder of your homedirectory called .venvs/

```
python3 -m venv ~/.venvs/discodos
source ~/.venvs/discodos/bin/activate
```

Double check if your environment is active and you are using the pip binary installed _inside_ your ~/.venvs/discodos/ directory.

`pip --version`

You should see something like this:

`pip 18.1 from /Users/jojo/.venvs/discodos/lib/python3.7/site-packages/pip (python 3.7)`

Install the necessary dependencies into your environment!

`pip install -r ~/discodos/requirements.txt`

Now [initialize the database and set up the CLI tools](#initialize-the-database-and-set-up-the-cli-tools), then [configure Discogs API access](#configure-discogs-api-access)




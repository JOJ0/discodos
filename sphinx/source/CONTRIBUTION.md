<!-- omit in toc -->
# Contribution

- [Install development version](#install-development-version)
  - [Prerequisites](#prerequisites)
  - [Windows - Install to virtual environment](#windows---install-to-virtual-environment)
  - [macOS or Linux - Install to virtual environment](#macos-or-linux---install-to-virtual-environment)
  - [macOS or Linux - Install to user environment](#macos-or-linux---install-to-user-environment)


## Install development version

If you'd like to contribute to DiscoDOS development or just want the most "bleeding edge" version, you'll most likely want to install it tracking this repos master branch or your fork's feature branch. Follow the guides in this document to achieve that.

I usually try to keep things stable in the master branch. I use it myself on my production database, so it just has to work. Seldomely there will be major bugs that could corrupt your data. In any case make sure you use DiscoDOS' neet built-in backup/sync feature!).

DiscoDOS is written entirely in Python. The majority of time, it was coded on a MacOS X 10.13 machine with Python installed via homebrew, thus it's tested well on this platform. There are some users happily using it on Winodws 10 already. I myself develop and use it on Linux machines too, and it seems to work as good as on my Mac.

Basically it will run on any OS as long as the following prerequisites are met. Please report back in any case, wether it's working fine or you find things that seem unusual on your OS. Thanks a lot!


### Prerequisites

You need to have these software packages installed
* git
* Python version 3.6 or higher

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


### Windows - Install to virtual environment

_[Skip this chapter](#macos-or-linux---install-into-virtual-environment) if you are on macOS or Linux!_

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

Install the necessary dependencies into your environment:

`python3 setup.py develop`

Launch DiscoDOS' main command and follow the steps shown:

`disco`

_**Note: Make sure you always first activate your virtual environment when coming back to developing or using DiscoDOS:**_

`"%HOMEPATH%/python-envs/discodos/Scripts/activate.bat"`


### macOS or Linux - Install to virtual environment

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

Install the necessary dependencies into your virtual environment:

`python3 setup.py develop`

Some command wrappers should have been installed too. Verify if they exist inside your `~/.venvs/discodos/bin` directory:

```
which disco
which discosync
```

Launch DiscoDOS' main command and follow the steps shown:

`disco`

_**Note: Make sure you always first activate your virtual environment when coming back to developing or using DiscoDOS:**_

`source ~/.venvs/discodos/bin/activate`


### macOS or Linux - Install to user environment

This chapter describes how to install the DiscoDOS package into your user's Python environment which is better suitable for just _using_ it, rather than _contributing/developing_.

Install Python 3. On Debian based distros (Ubuntu, Linux Mint, ...), do something like this:

`apt install python3`

on RedHat based (Fedora, CentOS, ...):

`yum install python3`



Clone the latest development version from github:

```
cd
git clone https://github.com/JOJ0/discodos.git
cd discodos
```

Install DiscoDOS into your user's Python environment:

`pip install . -e`

Some command wrappers should have been installed. Verify if they exist:

```
which disco
which discosync
```

If `which` didn't find those commands, make sure your $PATH environment variable contains the path the wrappers where installed to. Usually this is `~/.local/bin/`

_Note: On Debian-based systems there might be a file `/usr/bin/disco` on your system already provided by package mono-devel, thus depending on the order of paths in `$PATH`, `/usr/bin/disco` might be found before the DiscoDOS wrapper. Change `$PATH` to first search in `~/.local/bin` (export it in `.zshrc`, or `.bashrc` or whatever shell you are using)_

Launch DiscoDOS' main command:

`disco`

On first launch, `disco` will create a configuration file for you. To access your Discogs collection, an access token has to be generated and put into the file. Follow the steps in chapter [Configure Discogs API access](INSTALLATION.md#configure-discogs-api-access), then come back here!

Now that you've put the token into the configuration file, DiscoDOS completes setup by creating a local database (the DiscoBASE).

**Note: In case you are updating from a previous DiscoDOS version, your data will be kept and your database's schema might be upgraded automatically**

If the connection to Discogs is working, setup asks you to view a little tutorial teaching you how it works - hit enter and follow the steps.

Your starting point for further documentation is the [Quickstart Guide](QUICKSTART.md#importing-your-discogs-collection). Your next logical step is importing your Discogs collection.

**Note: The `disco` and `discosync` commands are now installed globally and will work in any terminal emulator.**

**Note: DiscoDOS generates the following files which are kept in `~/.discodos/`:**

 - The DiscoDOS configuration file (`config.yaml`)
 - The DiscoBASE (`discobase.db`)
 - A logfile (`debug.log`)


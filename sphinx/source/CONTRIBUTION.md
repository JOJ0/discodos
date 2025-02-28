<!-- omit in toc -->
# Contributing

Get in contact via Matrix @jojo:peek-a-boo.at or just open a pull-request or an issue already and let's move from there. Everything is possible.

## Setting up a development environment

### Create a virtual environment

Create and activate a virtual Python environment! The environment will be saved inside a hidden subfolder of your homedirectory called .venvs/

```sh
python3 -m venv ~/.venvs/discodos
source ~/.venvs/discodos/bin/activate
```

Double check if your environment is active and you are using the pip binary installed _inside_ your ~/.venvs/discodos/ directory.

`pip --version`


### Install the latest development version from Git

Jump to your homedirectory, clone the repo and change into the cloned repo directory.

```sh
cd
git clone https://github.com/JOJ0/discodos.git
cd discodos
```

Install DiscoDOS and its dependencies into your environment:

`pip install -e .`

### Verify installation

Some command wrappers should have been installed too. Verify if they exist inside your `~/.venvs/discodos/bin` directory:

```sh
which dsc
which discosync
```

Launch DiscoDOS' main command and follow the steps shown:

`dsc`

:::{tip}
Make sure you always first activate your virtual environment when coming back to developing or using DiscoDOS.
:::

`source ~/.venvs/discodos/bin/activate`

# The geekiest Vinyl DJ playlist tool on the planet

This tool helps a Vinyl DJ to remember and analyze what they played in their sets, or what they could possibly play in the future. It's based on data pulled from one's [Discogs](https://www.discogs.com) records collection.

## Initial Setup

Create and activate a virtual Python environment, using the venv-tool of your choice.

On Linux and Mac you could possibly use virtualenv.

`virtualenv discodos; source discodos/bin/activate`

Install the necessary dependencies into your environment!

`pip install -r requirements.txt`

The setup script creates an empty database.

`./setup.py`

You should find a file named `discobase.db` inside the root of your discodos folder.

Create a new mix.

`./cli.py mix -c new_mix_name`

View your mix.

`./cli.py new_mix_name`

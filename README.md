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

`./cli.py mix new_mix_name`

To access your Discogs collection you need to generate an API access token.

- Login to discogs.com
- Click your avatar (top right)
- Select _Settings_
- Switch to section _Developers_
- Click _Generate new token_
- Create a file named `config.yaml` inside the discodos root dir (next to the files `setup.py` and `cli.py`) that looks like this:

 ```
 ---
 discogs_token: "XDsktuOMNkOPxvNjerzCbvJIFhaWYwmdGPwnaySH"
 discogs_appid: "J0J0 Todos Discodos/0.0.2 +http://github.com/JOJ0"
 ```

Import your collection to the DiscoBASE

`./setup.py -i`

When the import is through you should be able to add your collection's tracks to the "mix" created above.

`./cli.py mix new_mix_name -a "Amon Tobin Killer Vanilla"`

Note that even though the tracks name actually is "The Killer's Vanilla" it will be found.

Be precise when asked for the track number on the record: A1 is not the same as A.

View your mix again, your track should be there, verbose mode shows that track and artist names are still missing.

`./cli.py mix new_mix_name -v`

Add some more tracks!

Now update your mix's tracks with data pulled from the Discogs API. If track numbers are not precise (eg A vs A1) data won't be found!

`./cli.py mix new_mix_name -u`

Use the verbose mode to see all the details pulled from Discogs.

`./cli.py mix new_mix_name -v`

Ask what more you could do with your mix and its tracks

`./cli.py mix new_mix_name --help`

You have two options to edit your mix's tracks. Eg to edit the third track in your mix you could either use

`./cli.py mix new_mix_name -e 3`

which edits _all_ fields, or you could select specific fields using the bulk edit option

`./cli.py mix new_mix_name -b trans_rating,bpm -p 3`

If you leave out -p 3 (the track position option) you just go through all of your mixes tracks and are asked to put data into the selected fields

`./cli.py mix new_mix_name -b trans_rating,bpm`
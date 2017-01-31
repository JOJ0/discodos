# discogs-get-collection

A Python script that grabs your [Discogs](https://www.discogs.com) records collection, the metadata of every release, and turns it into a CSV file that you can sort in a spreadsheets app, or process further if you modify the script.

Discogs themselves offer a feature to export CSV but it doesn't let you export specific fields from a release. In my case I mostly wanted to export the genres and styles of every disc I have, in order to sort records by genre more easily. With some tweaking you can make this export whatever metadata about the record you want, and you could sort directly from Python if needed (I just found Excel much faster for tweaking sorting options until I got it right).

## Usage

1) Get a personal access token [in your Discogs preference](https://www.discogs.com/settings/developers), and copy it inside the **vinylsget.py** file.

2) `pip install discogs_client`

3) `python3 vinylsget.py`

4) open `collection.csv` in your favourite spreadsheet editor.

## Todo

It's very basic, but it's a good starting point for similar projects, or if you are were bit unclear about how to use the Discogs Python library (I certainly was). One thing it doesn't do very well is handle metadata that's not excellently standardised; it shouldn't spit out errors but it might sometimes give something like Album instead of CD, 12" instead of 2xLP, the artist twice, compilations with a wrong artist name and so on.

Some of these things can probably be fixed, some of them are just down to bad tagging on Discogs and there's not much I can do about that.

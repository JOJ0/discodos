# pip install discogs_client

import discogs_client
import csv

userToken = ""

if userToken == "":
    exit("Whoops, you need to set your user token.")

d = discogs_client.Client("CollectionGenreClassifier/0.1 +http://github.com/victorloux",
                          user_token=userToken)

print("Gathering collection...")
me = d.identity()
itemsInCollection = [r.release for r in me.collection_folders[0].releases]
rows = []

print("Crunching data...")
for r in itemsInCollection:
    row = {}

    try:
        row['primaryGenre'] = r.genres[0]
        if len(r.genres) > 1:
            row['secondaryGenres'] = ", ".join(r.genres[1:])

        row['primaryStyle'] = r.styles[0]
        if len(r.styles) > 1:
            row['secondaryStyles'] = ", ".join(r.styles[1:])

        row['catalogNumber'] = r.labels[0].data['catno']
        row['artists'] = ", ".join(a.name for a in r.artists)
        row['format'] = r.formats[0]['descriptions'][0]

    except (IndexError, TypeError):
        None
        # @todo: normally these exceptions only happen if there's missing data
        # but ideally the program should check if values are missing, rather than
        # ignoring any exception resulting from trying

    row['title'] = r.title

    if r.year > 0:
        row['year'] = r.year

    rows.append(row)

print("Writing CSV...")
# Write to CSV
with open('collection.csv', 'w') as csvfile:
    csvfile.write('\ufeff')  # utf8 BOM needed by Excel

    fieldnames = ['format', 'primaryGenre', 'primaryStyle', 'secondaryGenres',
                  'secondaryStyles', 'catalogNumber', 'artists', 'title', 'year']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, restval='')

    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print("Done!")

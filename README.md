# The geekiest Vinyl DJ playlist tool on the planet

It's based on data pulled from your [Discogs](https://www.discogs.com) records collection. Stay tuned...

## Initial Setup

You just have to install all the dependencies, which can be found in the requirements.tx.

`pip install -r requirements.txt`

When all is set, you should run `python setup.py` for the initial db setup. 
When it is done, you should get the message `"All is Done!"`

After that you are all set to go. Create a new mix with: `python cli mix -c made_up_name`
View your mix with: `python cli.py made_up_name`



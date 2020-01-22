#!/usr/bin/env python

import sys
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
from discodos import log
from discodos.utils import *
import asyncio
#from codetiming import Timer

async def main():
    conf=Config()
    log.handlers[0].setLevel("INFO") # handler 0 is the console handler
    sync = Sync(conf.dropbox_token)
    await sync._async_init()
    await sync.backup()
    await sync.select_revision()

class Sync(object):
    def __init__(self, token):
        log.info("We are in __init__")
        self.token = token
        self.discobase = 'discobase.db'
        self.backuppath = '/discodos/discobase.db'

    #def __await__(self):
    #    log.info("We are in __await__")
    #    return self._async_init().__await__()

    async def _async_init(self):
        log.info("We are in _async_init")
        if (len(self.token) == 0): # Check for an access token
            log.error("Looks like you didn't add your access token.")
        await self._login()
        return self

    async def _login(self):
        log.info("We are in _login")
        # Create an instance of a Dropbox class, which can make requests to the API.
        log.info("Creating a Dropbox object...")
        self.dbx = dropbox.Dropbox(self.token)
        #print("One")
        await asyncio.sleep(1)
        #print("Two")

        # Check that the access token is valid
        try:
            self.dbx.users_get_current_account()
            return True
        except AuthError:
            log.error("ERROR: Invalid access token; try re-generating an "
                "access token from the app console on the web.")
            return False

    # Uploads contents of self.discobase to Dropbox
    async def backup(self):
        with open(self.discobase, 'rb') as f:
            # We use WriteMode=overwrite to make sure that the settings in the file
            # are changed on upload
            print("Uploading " + self.discobase + " to Dropbox as " + self.backuppath + "...")
            try:
                self.dbx.files_upload(f.read(), self.backuppath, mode=WriteMode('overwrite'))
                log.info("File successfully backuped or already up to date.")
            except ApiError as err:
                # This checks for the specific error where a user doesn't have
                # enough Dropbox space quota to upload this file
                if (err.error.is_path() and
                        err.error.get_path().reason.is_insufficient_space()):
                    sys.exit("ERROR: Cannot back up; insufficient space.")
                elif err.user_message_text:
                    print(err.user_message_text)
                    sys.exit()
                else:
                    print(err)
                    sys.exit()

    # Restore the local and Dropbox files to a certain revision
    async def restore(self, rev=None):
        # Restore the file on Dropbox to a certain revision
        print("Restoring " + self.backuppath + " to revision " + rev + " on Dropbox...")
        self.dbx.files_restore(self.backuppath, rev)

        # Download the specific revision of the file at self.backuppath to self.discobase
        print("Downloading current " + self.backuppath + " from Dropbox, overwriting " + self.discobase + "...")
        self.dbx.files_download_to_file(self.discobase, self.backuppath, rev)

    # Look at all of the available revisions on Dropbox, and return the oldest one
    async def select_revision(self):
        # Get the revisions for a file (and sort by the datetime object, "server_modified")
        print("Finding available revisions on Dropbox...")
        entries = self.dbx.files_list_revisions(self.backuppath, limit=30).entries
        revisions = sorted(entries, key=lambda entry: entry.server_modified)

        for revision in revisions:
            print(revision.rev, revision.server_modified)

        # Return the oldest revision (first entry, because revisions was sorted oldest:newest)
        #return revisions[0].rev


# Create a backup of the current settings file
#backup()

# Change the user's file, create another backup
#change_local_file("updated")
#backup()

# Restore the local and Dropbox files to a certain revision
#to_rev = select_revision()
#restore(to_rev)

#print("Done!")


# __MAIN try/except wrap
if __name__ == "__main__":
    try:
        #main()
        asyncio.run(main())
    except KeyboardInterrupt:
        log.error('Program interrupted!')
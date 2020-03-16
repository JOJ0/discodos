#!/usr/bin/env python

import sys
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
from urllib3.exceptions import NewConnectionError
from requests.exceptions import ConnectionError
from discodos import log
from discodos.utils import print_help, ask_user, is_number, Config
import asyncio
#from codetiming import Timer
import argparse
from sys import argv
from webdav3.client import Client
from webdav3.client import WebDavException
from datetime import datetime
from dateutil.parser import parse
from shutil import copy2


def argparser(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
		"-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help="increase log verbosity (-v -> INFO level, -vv DEBUG level)")
    parser.add_argument(
		"-t", "--type", dest="sync_type",
        type=str, default='dropbox', choices=['dropbox', 'webdav'],
        help="select synchronisation type: dropbox (default) or webdav")
    parser_group1 = parser.add_mutually_exclusive_group()
    parser_group1.add_argument(
		"--backup",
        action='store_true',
        help="")
    parser_group1.add_argument(
		"--restore",
        action='store_true',
        help="")
    parser_group1.add_argument(
		"--show",
        action='store_true',
        help="")
    arguments = parser.parse_args(argv[1:])
    log.info("Console log_level currently set to {} via config.yaml or default.".format(
        log.handlers[0].level))
    # Sets log level to WARN going more verbose for each new -v.
    cli_level = max(3 - arguments.verbose_count, 0) * 10
    if cli_level < log.handlers[0].level: # 10 = DEBUG, 20 = INFO, 30 = WARNING
        log.handlers[0].setLevel(cli_level)
        log.warning("Console log_level override via cli (sync.py). Now set to {}.".format(
            log.handlers[0].level))
    return arguments

async def main():
    conf=Config()
    log.handlers[0].setLevel(conf.log_level) # handler 0 is the console handler
    args = argparser(argv)
    if args.sync_type == 'dropbox':
        sync = Dropbox_sync(conf.dropbox_token, conf.discobase.name)
        if args.backup:
            await sync._async_init()
            await sync.backup()
        elif args.restore:
            await sync._async_init()
            await sync.print_revisions()
            rev = ask_user('Which revision do you want to restore? ')
            try:
                await sync.restore(rev)
            except dropbox.stone_validators.ValidationError:
                log.error('Revision not valid.')
        elif args.show:
            await sync._async_init()
            await sync.print_revisions()
        else:
            log.error("Missing arguments.")
    else:
        log.info("webdav sync here")
        sync = Webdav_sync(conf.webdav_user, conf.webdav_password,
          conf.webdav_url, conf.discobase.name)
        if args.backup:
            sync.backup()


class Dropbox_sync(object):
    def __init__(self, token, db_file):
        log.info("We are in __init__")
        self.token = token
        self.discobase = db_file
        self.backuppath = '/discodos/{}'.format(db_file)

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
        try:
            self.dbx = dropbox.Dropbox(self.token)
        #except urllib3.exceptions.NewConnectionError:
        except requests.exceptions.ConnectionError:
            log.error("connecting to Dropbox.")
        #print("One")
        #await asyncio.sleep(1)
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
        #print("Restoring " + self.backuppath + " to revision " + rev + " on Dropbox...")
        #self.dbx.files_restore(self.backuppath, rev)

        # Download the specific revision of the file at self.backuppath to self.discobase
        print("Downloading current " + self.backuppath + " from Dropbox, overwriting " + self.discobase + "...")
        self.dbx.files_download_to_file(self.discobase, self.backuppath, rev)

    # Look at all of the available revisions on Dropbox, and return the oldest one
    async def print_revisions(self):
        # Get the revisions for a file (and sort by the datetime object, "server_modified")
        print("Finding available revisions on Dropbox...")
        entries = self.dbx.files_list_revisions(self.backuppath, limit=30).entries
        revisions = sorted(entries, key=lambda entry: entry.server_modified)

        for revision in revisions:
            print(revision.rev, revision.server_modified)

        # Return the oldest revision (first entry, because revisions was sorted oldest:newest)
        #return revisions[0].rev


class Webdav_sync(object):
    def __init__(self, user, password, url, db_file):
        log.info("We are in Webdav_sync.__init__")
        if user == '' or password == '' or url == '':
            log.error("Webdav config incomplete. Check config.yaml")
            raise SystemExit
        else:
            self.user = user
            self.password = password
            self.url = url
        self.discobase = db_file
        #self.backuppath = '/discodos/{}'.format(db_file)
        options = {
            'webdav_hostname': self.url,
            'webdav_login':    self.user,
            'webdav_password': self.password
        }
        self.client = Client(options)
        print(dir(self.client))
        print('')
        #print(self.client.is_dir('discodos'))
        #print(self.client.check(self.discobase))

    def backup(self):
        with open(self.discobase, 'rb') as f:
            #print("Uploading {} to Webserver as {} ...".format(self.discobase,
            #  self.backuppath))
            print("Uploading {} to {} ...".format(self.discobase, self.url))
            existing = False
            try:
                if self.client.check(self.discobase):
                    existing = True
                else:
                    existing = False
            except WebDavException as exception:
                print('Webserver returned: {}'.format(exception))
                raise SystemExit

            if existing:
                print('Backup already existing, moving file away ...'.format(
                    self.discobase))
                date_time = parse(self.client.info(self.discobase)['modified'])
                datestr = date_time.strftime('%Y-%m-%d_%H%M%S')
                bak_file_name = '{}_{}'.format(self.discobase, datestr)
                print('Backup will be called: {}\n'.format(bak_file_name))
                # check if backup file with name already existing and ask user for overwrite
                if self.client.check(bak_file_name):
                    # double check for file time??
                    #bak_file_time = parse(self.client.info(bak_file_name)['modified'])
                    yes_copy = ask_user('A backup named "{}" is already existing. Overwrite? '.format(bak_file_name))
                    if yes_copy:
                        #copy2(self.discobase, bak_file_name)) # local command also?
                        self.client.copy(remote_path_from=self.discobase, remote_path_to=bak_file_name)
                else: # backup with timestamp not existing yet
                        self.client.copy(remote_path_from=self.discobase, remote_path_to=bak_file_name)
                self.show_backups()
            else:
                print('Backup not existing yet, uploading ...')
                self.client.upload_sync(remote_path='{}'.format(self.discobase),
                                        local_path='{}'.format(self.discobase))
    def show_backups(self):
        print_help('\nExisting backups:')
        for resource in self.client.list():
            print(resource)
        print()

# __MAIN try/except wrap
if __name__ == "__main__":
    try:
        #main()
        asyncio.run(main())
    except KeyboardInterrupt:
        log.error('Program interrupted!')

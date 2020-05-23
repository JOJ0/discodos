#!/usr/bin/env python

import sys
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
from dropbox.dropbox import BadInputException
from urllib3.exceptions import NewConnectionError
from requests.exceptions import ConnectionError
from socket import gaierror

#from discodos import log
import logging
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
from pathlib import Path
import re
from os import utime

log = logging.getLogger('discodos')


def argparser(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
		"-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help="increase log verbosity (-v -> INFO level, -vv DEBUG level)")
    parser.add_argument(
		"-t", "--type", dest="sync_type",
        type=str, default='dropbox', choices=['dropbox', 'webdav', 'd', 'w'],
        help='''select synchronisation type: dropbox (default) or webdav;
                or just in short: d or w''')
    parser_group1 = parser.add_mutually_exclusive_group()
    parser_group1.add_argument(
		"-b", "--backup",
        action='store_true',
        help="")
    parser_group1.add_argument(
		"-r", "--restore",
        action='store_true',
        help="")
    parser_group1.add_argument(
		"-s", "--show",
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

def main():
    try:
        _main()
        #asyncio.run(_main())
    except KeyboardInterrupt:
        msg_int = 'DiscoDOS sync canceled (ctrl-c)'
        log.info(msg_int)
        print(msg_int)

def _main():
    conf=Config()
    log.handlers[0].setLevel(conf.log_level) # handler 0 is the console handler
    args = argparser(argv)
    if args.sync_type == 'dropbox' or args.sync_type == 'd':
        sync = Dropbox_sync(conf.dropbox_token, conf.discobase.name)
        if args.backup:
            #await sync._async_init()
            sync.backup()
        elif args.restore:
            #await sync._async_init()
            #try:
            #    sync.restore()
            #except dropbox.stone_validators.ValidationError:
            #    log.error('Revision not valid.')
            sync.restore()
        elif args.show:
            #await sync._async_init()
            sync.show_backups()
        else:
            log.error("Missing arguments.")
    else:
        sync = Webdav_sync(conf.webdav_user, conf.webdav_password,
          conf.webdav_url, conf.discobase.name)
        if args.backup:
            sync.backup()
        elif args.restore:
            sync.restore()
        elif args.show:
            sync.show_backups()

class Sync(object):
    def _local_mtime(self, filename): # returns a file's formatted mtime
        mod_local_dt = datetime.fromtimestamp(
                          Path(filename).stat().st_mtime)
        mod_local_str = mod_local_dt.strftime('%Y-%m-%d_%H%M%S')
        return mod_local_str

    def _filename_mtime(self, filename):
        local_mtime = self._local_mtime(filename)
        return '{}_{}'.format(filename, local_mtime)

    def _times_tuple(self, filename): # get epoch from file someth_YYYY-MM-DD_HHMMMSS
        time = re.split('[^\d]', filename)[-1]
        day = re.split('[^\d]', filename)[-2]
        month = re.split('[^\d]', filename)[-3]
        year = re.split('[^\d]', filename)[-4]
        filename_datepart = "{}{}{}{}".format(year, month, day, time)
        log.debug('Sync._times_tuple: filename_datepart: {}'.format(filename_datepart))
        if not filename_datepart:
            log.error(
              'Not a valid DiscoBASE backup (Format not name_yyyy-mm-dd_HHMMSS.db). Quitting.')
            raise SystemExit(1)
        mod_dt = datetime.strptime(filename_datepart, '%Y%m%d%H%M%S')
        mod_epoch = mod_dt.timestamp()
        log.debug('Sync._times_tuple: mod_epoch: {}'.format(mod_epoch))
        times_tuple = (mod_epoch, mod_epoch)
        return times_tuple

    def _touch_to_backupdate(self, restore_file_name):
        downloaded_file = Path(self.discobase) # ignore vscode error here
        mod_acc_times = self._times_tuple(restore_file_name)
        log.debug('Sync._touch_to_backupdate: mod_acc_times: {}'.format(mod_acc_times))
        try:
            utime(downloaded_file, mod_acc_times)
        except Exception as exc:
            log.error(
              'Error setting timestamp of restored file to original backupdate! {}'.format(exc))



class Dropbox_sync(Sync):
    def __init__(self, token, db_file):
        super().__init__()
        log.info("We are in __init__")
        self.token = token
        self.discobase = db_file
        # FIXME make configurable
        self.backuppath = '/discodos'
        self._login()

#    #def __await__(self):
    #    log.info("We are in __await__")
    #    return self._async_init().__await__()

    #async def _async_init(self):
    #    log.info("We are in _async_init")
    #    if (len(self.token) == 0): # Check for an access token
    #        log.error("Looks like you didn't add your access token.")
    #    await self._login()
    #    return self
#

    def _login(self):
        log.info("We are in _login")
        log.info("Creating a Dropbox object...")
        # doesn't have to be catched! doesn't connect!
        try:
            self.dbx = dropbox.Dropbox(self.token)
        except BadInputException:
            log.error("Dropbox token is missing in config.yaml.")
            raise SystemExit(1)
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
        except NewConnectionError:
            log.error("connecting to Dropbox. (NewConnectionError)")
            raise SystemExit(1)
        except ConnectionError:
            log.error("connecting to Dropbox. (ConnectionError)")
            raise SystemExit(1)
        except gaierror:
            log.error("connecting to Dropbox. (gaierror)")
            raise SystemExit(1)
        except:
            log.error("connecting to Dropbox. (Uncatched exception)")
            raise SystemExit(1)

    def exists(self, path):
        try:
            self.dbx.files_get_metadata(path)
            return True
        except ApiError as apierr:
            #print(dir(apierr.error.get_path()))
            if apierr.error.get_path().is_not_found() == True:
                log.debug('Dropbox_sync.exits: File not yet existing.')
                return False
            log.error(
              'Dropbox ApiError: Exception on file exists check: {}'.format(
                apierr))
            return True

    def backup(self):
        bak_file_name = self._filename_mtime(self.discobase)
        full_bak_path = '{}/{}'.format(self.backuppath, bak_file_name)
        print("Uploading as {} to {}".format(bak_file_name, self.backuppath))
        if self.exists('{}/{}'.format(self.backuppath, bak_file_name)):
            log.warning('Backup existing. Won\'t overwrite "{}" '.format(
                    bak_file_name))
        else:
            print('Backup not existing yet, uploading ...')
            with open(self.discobase, 'rb') as f:
                try:
                    self.dbx.files_upload(f.read(), full_bak_path,
                          mode=WriteMode('overwrite'))
                    log.debug(
                      "File successfully backuped or already up to date.")
                except ApiError as err:
                    # This checks for the specific error where a user doesn't have
                    # enough Dropbox space quota to upload this file
                    if (err.error.is_path() and
                            err.error.get_path().reason.is_insufficient_space()):
                        log.error('Cannot back up; insufficient space. Quitting.')
                        raise SystemExit(1)
                    elif err.user_message_text:
                        print(err.user_message_text)
                        raise SystemExit(1)
                    else:
                        print(err)
                        raise SystemExit(1)
            self.show_backups()

    def show_backups(self, restore=False):
        if not restore:
            print('\nExisting backups:')
        all_files = self.dbx.files_list_folder(path=self.backuppath)
        relevant_files = []

        for resource in all_files.entries:
            relevant_files.append(resource)

        for j, item in enumerate(relevant_files): 
            file = '({}) - {}'.format(j, item.name)
            print(file)
            #print(item.client_modified)
            #print(item.server_modified)

        if restore:
            restore_id = ask_user('Restore backup #: ')
            try:
                restore_file = relevant_files[int(restore_id)]
            except ValueError:
                log.warning('Nothing to restore!')
                raise SystemExit
            except IndexError:
                log.warning('Non-existent ID. Nothing to restore!')
                raise SystemExit
            print('Restoring Backup {}...'.format(restore_file.name)) # name attribute
            return restore_file # return the whole object here
        print()

    def restore(self):
        print('\nWhich backup would you like to restore?')
        restore_file = self.show_backups(restore = True)
        full_bak_path = '{}/{}'.format(self.backuppath, restore_file.name)
        overwrite = ask_user("Download backup and overwrite local file {} (y/N)? ".format(
              self.discobase))
        if overwrite.lower() == 'y':
            self.dbx.files_download_to_file(self.discobase, full_bak_path,
                  restore_file.rev)
            self._touch_to_backupdate(restore_file.name)


class Webdav_sync(Sync):
    def __init__(self, user, password, url, db_file):
        super().__init__()
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
        #print(dir(self.client))
        #print('')
        #print(self.client.is_dir('discodos'))
        #print(self.client.check(self.discobase))

    def _webdav_mtime(self, filename): # we currently don't need this, put to func anyway
        mod_server_dt = parse(self.client.info(filename)['modified'])
        mod_server_str = mod_server_dt.strftime('%Y-%m-%d_%H%M%S')
        #if mod_local_str != mod_server_str:
        #    print('Local and server discobase.db modification time diverge.')
        #    print(mod_local_str)
        #    print(mod_server_str)
        return mod_server_str

    def backup(self):
        # check file stats on local machine
        bak_file_name = self._filename_mtime(self.discobase)
        print("Uploading as {} to {}".format(bak_file_name, self.url))
        existing = False
        try:
            if self.client.check(bak_file_name):
                existing = True
            else:
                existing = False
        except WebDavException as exception:
            log.error('Webserver returned: {}'.format(exception))
            raise SystemExit

        if existing:
            log.warning('Backup existing. Won\'t overwrite "{}" '.format(
                    bak_file_name))
        else:
            print('Backup not existing yet, uploading ...')
            self.client.upload_sync(remote_path='{}'.format(bak_file_name),
                                    local_path='{}'.format(self.discobase))

        self.show_backups()
        return True

    def show_backups(self, restore = False):
        if not restore:
            print('\nExisting backups:')
        #relevant_files = self.client.list()[1:] # leave out first item, it's the containing folder
        all_files = self.client.list()
        relevant_files = []
        for i, resource in enumerate(all_files):
            re_result = re.search('.*/$', resource)
            log.debug('Sync: Folder regex matched: {}'.format(re_result))
            if re_result: # skip all folders
                log.debug('Sync: Skipping resource: {}'.format(all_files[i]))
            else: # add files to new list
                relevant_files.append(resource)

        for j, file in enumerate(relevant_files):
            file = '({}) - {}'.format(j, file)
            print(file)

        if restore:
            restore_id = ask_user('Restore backup #: ')
            try:
                restore_file = relevant_files[int(restore_id)]
            except ValueError:
                log.warning('Nothing to restore!')
                raise SystemExit
            except IndexError:
                log.warning('Non-existent ID. Nothing to restore!')
                raise SystemExit
            print('Restoring Backup {}...'.format(restore_file))
            return restore_file
        print()

    def restore(self):
        print('\nWhich backup would you like to restore?')
        restore_filename = self.show_backups(restore = True)
        overwrite = ask_user("Download backup and overwrite local file {} (n)? ".format(
            self.discobase))
        if overwrite.lower() == 'y':
            self.client.download_sync(remote_path='{}'.format(restore_filename),
                                      local_path='{}'.format(self.discobase))
            self._touch_to_backupdate(restore_filename)

# __MAIN try/except wrap
if __name__ == "__main__":
    main()

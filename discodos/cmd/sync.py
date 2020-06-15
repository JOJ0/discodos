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
from discodos.utils import print_help, ask_user, is_number
from discodos.config import Config
import asyncio
#from codetiming import Timer
import argparse
from sys import argv
from webdav3.client import Client
from webdav3.exceptions import WebDavException
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
        sync = Dropbox_sync(conf.dropbox_token, conf.discobase)
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
          conf.webdav_url, conf.discobase)
        if args.backup:
            sync.backup()
        elif args.restore:
            sync.restore()
        elif args.show:
            sync.show_backups()

class Sync(object):
    def _get_local_mtime(self, fileobj): # returns a file's formatted mtime
        mod_local_dt = datetime.fromtimestamp(
                          fileobj.stat().st_mtime)
        mod_local_str = mod_local_dt.strftime('%Y-%m-%d_%H%M%S')
        return mod_local_str

    def _get_local_mtime_dt(self, fileobj): # returns file's mtime as datetime obj
        mod_local_dt = datetime.fromtimestamp(
                          fileobj.stat().st_mtime)
        return mod_local_dt

    def _get_fileobj_mtime(self, fileobj):
        local_mtime = self._get_local_mtime(fileobj)
        return '{}_{}'.format(fileobj.name, local_mtime)

    def _get_times_tuple(self, filestr): # get epoch from string someth_YYYY-MM-DD_HHMMMSS
        time = re.split('[^\d]', filestr)[-1]
        day = re.split('[^\d]', filestr)[-2]
        month = re.split('[^\d]', filestr)[-3]
        year = re.split('[^\d]', filestr)[-4]
        filestr_date_digits = "{}{}{}{}".format(year, month, day, time)
        log.debug('Sync._get_times_tuple: filestr_date_digits: {}'.format(filestr_date_digits))
        if not filestr_date_digits:
            log.error(
              'Not a valid DiscoBASE backup (Format not name_yyyy-mm-dd_HHMMSS.db). Quitting.')
            raise SystemExit(1)
        mod_dt = datetime.strptime(filestr_date_digits, '%Y%m%d%H%M%S')
        mod_epoch = mod_dt.timestamp()
        log.debug('Sync._get_times_tuple: mod_epoch: {}'.format(mod_epoch))
        times_tuple = (mod_epoch, mod_epoch)
        return times_tuple

    def _touch_to_backupdate(self, restore_filenamestr):
        downloaded_file = self.discobase # ignore vscode error here
        mod_acc_times = self._get_times_tuple(restore_filenamestr)
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
                #log.debug('Dropbox_sync.exits: File not yet existing.')
                return False
            log.error(
              'Dropbox ApiError: Exception on file exists check: {}'.format(
                apierr))
            return True

    def get_client_modified(self, path):
        try:
            mod_time = self.dbx.files_get_metadata(path).client_modified
            log.debug('Dropbox_sync.get_client_modified: {}.'.format(mod_time))
            return mod_time
        except ApiError as apierr:
            #print(dir(apierr.error.get_path()))
            if apierr.error.get_path().is_not_found() == True:
                log.debug('Dropbox_sync.get_client_modified: File not yet existing.')
            log.error(
              'Dropbox ApiError: Exception while getting client mod time {}'.format(
                apierr))
            return None

    def delete(self, target_file):
        try:
            log.info("Dropbox_sync.delete: Deleting {}.".format(
                  target_file))
            self.dbx.files_delete_v2(target_file)
        except ApiError as err:
            # just info log error - don't bother user, it's a future feature
            log.info(err)

    def copy(self, source_file, target_file):
        try:
            log.info("Dropbox_sync.copy: Copying {} to {}.".format(
                  source_file, target_file))
            self.dbx.files_copy_v2(source_file, target_file)
        except ApiError as err:
            # just info log error - don't bother user, it's a future feature
            log.info(err)

    def backup(self):
        bak_file_name = self._get_fileobj_mtime(self.discobase)
        full_bak_path = '{}/{}'.format(self.backuppath, bak_file_name)
        copy_file_path = '{}/{}'.format(self.backuppath, self.discobase.name)
        print("Uploading as {} to {}".format(bak_file_name, self.backuppath))
        if self.exists('{}/{}'.format(self.backuppath, bak_file_name)):
            log.warning('Backup existing. Won\'t overwrite "{}" '.format(
                    bak_file_name))
            #log.info('Exixting backup metadata: {}'.format(
            #    self.dbx.files_get_metadata(full_bak_path)))
        else:
            print('Backup not existing yet, uploading ...')
            with open(self.discobase, 'rb') as f:
                try:
                    self.dbx.files_upload(f.read(), full_bak_path,
                      mode=WriteMode('overwrite'),
                      client_modified=self._get_local_mtime_dt(self.discobase))
                    m_success = 'Dropbox_sync.backup: File successfully backuped '
                    m_success+= 'or already up to date.'
                    log.debug(m_success)
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

                # make a copy of the just uploaded file, named without date!
                # this eases accessing the latest discobase for other apps
                if self.exists(copy_file_path):
                    m_exists = 'Dropbox_sync.backup: Latest discobase file '
                    m_exists+= 'already existing, checking client_modified times.'
                    log.info(m_exists)
                    mod_time_bak = self.get_client_modified(full_bak_path)
                    mod_time_copy = self.get_client_modified(copy_file_path)
                    if mod_time_bak <= mod_time_copy:
                        m_newer = 'Dropbox_sync.backup: Timestamp of latest discobase '
                        m_newer+= 'file is newer than or the same as just uploaded file. '
                        m_newer+= 'Not overwriting.'
                        log.info(m_newer)
                    else:
                        m_older = 'Dropbox_sync.backup: Timestamp of latest discobase '
                        m_older+= 'file is older than just uploaded file. Overwriting!'
                        log.info(m_older)
                        self.delete(copy_file_path)
                        self.copy(full_bak_path, copy_file_path)
                else:
                    m_not_existing = 'Dropbox_sync.backup: Latest discobase '
                    m_not_existing+= 'file is not existing yet, copying.'
                    log.info(m_not_existing)
                    self.copy(full_bak_path, copy_file_path)
        # in any case, show list of existing backups
        self.show_backups()
        return True

    def show_backups(self, restore=False):
        if not restore:
            print('\nExisting backups:')
        all_files = self.dbx.files_list_folder(path=self.backuppath)
        relevant_files = []

        for resource in all_files.entries:
            if re.search('_(\d+)-(\d+)-(\d+)_(\d+)$', resource.name):
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
            print('Restoring backup {}...'.format(restore_file.name)) # name attribute
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
        bak_file_name = self._get_fileobj_mtime(self.discobase)
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

        # in any case, show list of existing backups
        self.show_backups()
        return True

    def show_backups(self, restore = False):
        if not restore:
            print('\nExisting backups:')
        #relevant_files = self.client.list()[1:] # leave out first item, it's the containing folder
        all_files = self.client.list()
        all_files.sort() # sorts by name
        relevant_files = []
        for i, resource in enumerate(all_files):
            if re.search('_(\d+)-(\d+)-(\d+)_(\d+)$', resource):
                relevant_files.append(resource)
            else:
                log.debug('Sync: Skipping resource: {}'.format(all_files[i]))

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
            print('Restoring backup {}...'.format(restore_file))
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

"""Module for trigger on file related events.
"""

import time
import tempfile
import shutil
import hashlib
import datetime
import os
import logging
import types

from ox_mon.common import configs, interface, stubs

try:
    import inotify.adapters
    import inotify.constants
except Exception as problem:  # pylint: disable=broad-except
    inotify = types.SimpleNamespace(  # pylint: disable=invalid-name
        adapters=stubs.GenericModuleStub(
            'adapters', str(problem), 'inotify'))
    inotify.adapters.Inotify = inotify.adapters.make_complainer('Inotify')


class FileWatchCopy(interface.OxMonTask):
    """Trigger to copy files when they are created or modified.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_loops = None

    @classmethod
    def options(cls):
        logging.debug('Making options for %s', cls)
        result = configs.BASIC_OPTIONS + [
            configs.OxMonOption(
                'watch', default=None, required=True, help=(
                    'Directory to watch for changes.')),
            configs.OxMonOption(
                'archive', default=None, required=True, help=(
                    'Directory to copy changes to.')),
            ]
        return result

    def _loop(self):
        """Check disk usage.
        """

        for key, name in [('archive', self.config.archive),
                          ('watch', self.config.watch)]:
            if not (name and os.path.exists(name)):
                raise ValueError('Directory %s = "%s" must exists.' % (
                    key, name))
            if not os.path.isdir(name):
                raise ValueError('%s %s must be a directory' % (
                    name, key))

        inote = inotify.adapters.InotifyTree(self.config.watch, (
            inotify.constants.IN_CLOSE_WRITE |
            inotify.constants.IN_CREATE |
            inotify.constants.IN_MOVED_TO |
            inotify.constants.IN_MOVE_SELF))

        for event in inote.event_gen(yield_nones=False):
            (header, type_names, path, filename) = event
            self._handle_event(header, type_names, path, filename)
            if self.max_loops is not None:
                self.max_loops -= 1
                if self.max_loops >= 0:
                    logging.info('%i loops left', self.max_loops)
                else:
                    logging.warning('Stopping loop')
                    break

    def _handle_event(self, header, type_names, path, filename):
        logging.debug('HEADER=%s', str(header))
        logging.info("PATH=[%s] FILENAME=[%s] EVENT_TYPES=%s",
                     path, filename, type_names)
        my_fname = os.path.join(path, filename)
        if self._handled_delete(my_fname, type_names):
            return
        if os.path.isdir(my_fname):
            logging.info('Skip directory %s', my_fname)
            return
        my_fd, tname = tempfile.mkstemp()
        os.close(my_fd)
        self._do_copy(my_fname, tname)

    @staticmethod
    def _handled_delete(my_fname: str, type_names) -> bool:
        result = False
        if type_names == ['IN_DELETE']:  # only deleting file
            for stime in [1, 2, 4]:
                if not os.path.exists(my_fname):
                    logging.info('Skip %s since it was deleted', my_fname)
                    result = True
                    break
                logging.debug('sleep %s to wait for %s deletion',
                              stime, my_fname)
                time.sleep(stime)
            else:
                logging.error('Got delete for %s but it was not deleted',
                              my_fname)
        return result

    def _do_copy(self, my_fname, tname):
        logging.info('Copying %s to temp file %s', my_fname, tname)
        if not os.path.exists(my_fname):
            logging.error('Could not copy %s since it is gone!', my_fname)
            return
        shutil.copy(my_fname, tname)  # copy to tmp file first for safety
        hash_dir, my_utc = self.prep_destination(tname)
        if os.path.exists(os.path.join(hash_dir, 'main.data')):
            logging.info('main data already exists in dir %s', hash_dir)
        else:
            logging.info('Copying %s to %s', tname,
                         os.path.join(hash_dir, 'main.data'))
            shutil.copy(tname, os.path.join(hash_dir, 'main.data'))

        with open(os.path.join(hash_dir, 'names.txt'), 'a') as my_fd:
            my_fd.write('%s: %s\n' % (my_utc, my_fname))
            logging.info('At utc %s saved %s', my_utc, my_fname)
        os.remove(tname)

    def prep_destination(self, tname: str):
        """Make destination to store file and return hash and utc timestamp.

        :param tname:    String name for path to file.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        :return:  The pair (utc, hash_dir) where utc is a string timestamp
                  based on UTC time and hash_dir is a path to the directory
                  to store files with the hash for tname (hash_dir is
                  created if necessary).

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:  Prepare a place to store the file.

        """
        my_utc, my_hash = self.make_utc_and_hash(tname)
        hash_dir = os.path.join(self.config.archive, my_hash)
        try:
            os.mkdir(hash_dir)
        except FileExistsError as prob:
            logging.info('Ignoring %s', str(prob))
        assert os.path.exists(hash_dir)
        return hash_dir, my_utc

    @staticmethod
    def make_utc_and_hash(fname: str):
        """Make and return utc timestamp and hash string.

        :param fname:    String name for path to file.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        :return:  The pair (utc, hash) where utc is a string timestamp
                  based on UTC time and hash is the md5 hash of the file.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:  Get UTC timestamp and hash of file.

        """
        utc = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        md5 = hashlib.md5()
        with open(fname, 'rb') as my_fd:
            while True:
                data = my_fd.read(65536)
                if not data:
                    break
                md5.update(data)
        return utc, md5.hexdigest()

    def _do_task(self):
        return self._loop()

"""Module for trigger on file related events.
"""

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

            logging.debug('HEADER=%s', str(header))
            logging.info("PATH=[%s] FILENAME=[%s] EVENT_TYPES=%s",
                         path, filename, type_names)
            my_fname = os.path.join(path, filename)
            if os.path.isdir(my_fname):
                logging.info('Skip directory %s', my_fname)
                continue
            my_fd, tname = tempfile.mkstemp()
            os.close(my_fd)
            logging.info('Copying %s to temp file %s', my_fname, tname)
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
        if not os.path.exists(hash_dir):
            os.mkdir(hash_dir)
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

"""Some simple basic tests for triggers.
"""

import os
import time
import logging
import sys
import unittest
import subprocess
import shutil
import tempfile


class TestBasis(unittest.TestCase):
    """Simple test cases for file triggers
    """

    def __init__(self, *args, **kwargs):
        self.archive = None
        self.watch = None
        self.proc = None
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.archive = tempfile.mkdtemp()
        self.watch = tempfile.mkdtemp()
        logging.info('Starting subprocess for trigger.')
        self.proc = subprocess.Popen(
            [sys.executable, '-m', 'ox_mon.ui.cmd_line',
             'trigger', 'fwatch',
             '--archive', self.archive, '--watch', self.watch],
            env=os.environ.copy())
        time.sleep(1)  # give watch time to setup

    def tearDown(self):
        for item in [self.archive, self.watch]:
            if item and os.path.exists(item):
                logging.info('Removing %s', item)
                shutil.rmtree(item)
        if self.proc:
            self.proc.kill()
            self.proc.wait()
            self.proc = None

    def test_delete(self):  # pylint: disable=no-self-use
        """Simple test that deletions do not cause trouble.
        """
        tdir = tempfile.mkdtemp(dir=self.watch)
        time.sleep(1)
        fname = os.path.join(tdir, 'test.txt')
        with open(fname, 'w') as my_fd:
            my_fd.write('test data')
        time.sleep(1)
        my_hash = os.listdir(self.archive)[0]
        content = open(os.path.join(
            self.archive, my_hash, 'main.data')).read()
        self.assertEqual(content, 'test data')

        # Now test removing original file did not cause problems
        os.remove(fname)
        time.sleep(1)
        content = open(os.path.join(
            self.archive, my_hash, 'main.data')).read()
        self.assertEqual(content, 'test data')
        shutil.rmtree(tdir)

        # Now test that watching still happening
        my_hash = 'dd18bf3a8e0a2a3e53e2661c7fb53534'
        if os.path.exists(os.path.join(self.archive, my_hash)):
            shutil.rmtree(os.path.join(self.archive, my_hash))
        time.sleep(1)
        self.assertFalse(os.path.exists(os.path.join(self.archive, my_hash)))

        with open(os.path.join(self.watch, 'other.txt'), 'w') as my_fd:
            my_fd.write('test.txt')
        time.sleep(1)
        content = open(os.path.join(
            self.archive, my_hash, 'main.data')).read()
        self.assertEqual(content, 'test.txt')
        self.assertEqual(os.listdir(os.path.join(self.archive, my_hash)), [
            'names.txt', 'main.data'])
        self.assertTrue(self.proc.returncode is None)

    def test_simple(self):  # pylint: disable=no-self-use
        """Simple test of basic triggers
        """
        with open(os.path.join(self.watch, 'test.txt'), 'w') as my_fd:
            my_fd.write('test.txt')
        time.sleep(1)
        self.assertTrue(os.listdir(self.archive))
        my_hash = 'dd18bf3a8e0a2a3e53e2661c7fb53534'
        self.assertEqual([my_hash], os.listdir(self.archive))
        self.assertEqual(os.listdir(os.path.join(self.archive, my_hash)), [
            'names.txt', 'main.data'])
        tdir = tempfile.mkdtemp(dir=self.watch)
        time.sleep(1)
        with open(os.path.join(tdir, 'test.txt'), 'w') as my_fd:
            my_fd.write('test.txt')
        self.assertEqual([my_hash], os.listdir(self.archive))
        self.assertEqual(os.listdir(os.path.join(self.archive, my_hash)), [
            'names.txt', 'main.data'])
        time.sleep(1)
        content = open(os.path.join(
            self.archive, my_hash, 'names.txt')).read().strip().split('\n')
        self.assertEqual(len(content), 4)


if __name__ == '__main__':
    unittest.main()

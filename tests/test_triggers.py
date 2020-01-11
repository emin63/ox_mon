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
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.archive = tempfile.mkdtemp()
        self.watch = tempfile.mkdtemp()

    def tearDown(self):
        for item in [self.archive, self.watch]:
            if item and os.path.exists(item):
                logging.info('Removing %s', item)
                shutil.rmtree(item)

    def test_simple(self):  # pylint: disable=no-self-use
        """Simple test of basic triggers
        """
        logging.info('Starting subprocess for trigger.')
        proc = subprocess.Popen(
            [sys.executable, '-m', 'ox_mon.ui.cmd_line',
             'trigger', 'fwatch',
             '--archive', self.archive, '--watch', self.watch],
            env=os.environ.copy())
        time.sleep(1)  # give watch time to setup
        with open(os.path.join(self.watch, 'test.txt'), 'w') as my_fd:
            my_fd.write('test.txt')
        time.sleep(1)
        self.assertTrue(os.listdir(self.archive))
        my_hash = 'dd18bf3a8e0a2a3e53e2661c7fb53534'
        self.assertEqual([my_hash], os.listdir(self.archive))
        self.assertEqual(os.listdir(os.path.join(self.archive, my_hash)), [
            'names.txt', 'main.data'])
        proc.kill()
        proc.wait()


if __name__ == '__main__':
    unittest.main()

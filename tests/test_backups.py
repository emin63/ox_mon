"""Some simple basic tests for ox_mon backups
"""

import sys
import os
import tempfile
import unittest

from click.testing import CliRunner

from ox_mon.checking import apt_checker
from ox_mon.common import configs
from ox_mon.ui import cmd_line


class TestBackups(unittest.TestCase):
    """Simple test cases for backup tools.
    """

    def test_rsync_backup(self):  # pylint: disable=no-self-use
        """Simple test of basic rsync backup.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, 'src')
            dst = os.path.join(tmpdir, 'dst')
            os.mkdir(src)
            os.mkdir(dst)
            with open(os.path.join(src, 'test.txt'), 'w') as fdesc:
                fdesc.write('some test data')
            with open(os.path.join(src, 'example.txt'), 'w') as fdesc:
                fdesc.write('example data')
            runner = CliRunner()
            my_cmd = ['backup', 'rsync', '--source', src, '--dest', dst]
            result = runner.invoke(cmd_line.main, my_cmd)
            self.check_match(src, dst)

            # Now remove a file and make sure things match
            os.remove(os.path.join(src, 'test.txt'))
            my_cmd = ['backup', 'rsync', '--source', src, '--dest', dst]
            result = runner.invoke(cmd_line.main, my_cmd)
            self.assertEqual(result.exit_code, 0)
            self.check_match(src, dst)

    def check_match(self, src, dst):
        "Check src and dst directories match."

        for name in os.listdir(src):
            src_data = open(os.path.join(src, name), 'r').read()
            dst_data = open(os.path.join(dst, os.path.basename(src),
                                         name), 'r').read()
            self.assertEqual(src_data, dst_data)



if __name__ == '__main__':
    unittest.main()

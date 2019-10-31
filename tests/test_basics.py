"""Some simple basic tests for ox_mon.
"""

import sys
import os
import tempfile
import unittest

from click.testing import CliRunner

from ox_mon.checking import apt_checker
from ox_mon.common import configs
from ox_mon.ui import cmd_line


class TestAptShellChecker(unittest.TestCase):
    """Simple test cases for apt shell checker.
    """

    def test_apt_shell_checker(self):  # pylint: disable=no-self-use
        """Simple test of basic apt shell checker.
        """
        my_config = configs.BasicConfig(age_in_days=1e100000, limit=1e100,
                                        notifier=['loginfo'])
        chk = apt_checker.AptShellChecker(my_config)
        data = chk.run()
        self.assertEqual(data, 'No packages need updating.')

    def test_apt_via_cmdline(self):  # pylint: disable=no-self-use
        """Simple test of basic apt shell checker using click CLI runner
        """
        runner = CliRunner()
        my_cmd = ['check', 'apt', '--notifier', 'loginfo', '--notifier',
                  'echo', '--age-in-days', 1e10000, '--limit', 10000]
        result = runner.invoke(cmd_line.main, my_cmd)
        self.assertEqual(result.exit_code, 0)

    def test_apt_force_notify(self):  # pylint: disable=no-self-use
        """Simple test of basic apt shell checker to force notification.

        This is helpful because it verifies at least basic notifiers work.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_line.main, [  # use age 0 to force notify
            'check', 'apt', '--notifier', 'echo', '--age-in-days', '0'])
        self.assertEqual(result.exit_code, 1)

    def disk_checker(  # pylint: disable=no-self-use
            self, max_pct, tool='shutil'):
        """Simple test of basic disk checker.
        """
        runner = CliRunner()
        my_cmd_line = ['check', 'disk', '--notifier', 'loginfo',
                       '--max-used-pct', max_pct]
        if tool:
            my_cmd_line.extend(['--tool', tool])
        result = runner.invoke(cmd_line.main, my_cmd_line)
        return result

    def test_disk_checker(self):  # pylint: disable=no-self-use
        "Test disk checker success and failure."
        proc = self.disk_checker('99')
        self.assertEqual(proc.exit_code, 0)
        proc = self.disk_checker('0', tool='shutil')
        self.assertEqual(proc.exit_code, 1)
        proc = self.disk_checker('99', tool='psutil')
        self.assertEqual(proc.exit_code, 0)

    def test_clamscan_hit(self):  # pylint: disable=no-self-use
        """Test case where clamscan should find a hit.

WARNING:   This will write a virust test file to a temp file to
WARNING:   verify the hit and then try to delete it. If you have
WARNING:   another virus scanner running, it may get upset.
        """
        vir_start = r'X5O!P%@AP[4\PZX54(P^)7CC)7}$EI'
        vir_mid = r'CAR-STANDARD-ANTIV'
        vir_end = r'IRUS-TEST-FILE!$H+H*'
        vfile = tempfile.mktemp(suffix='_eicar_virus_test.txt')
        try:
            open(vfile, 'w').write(vir_start + vir_mid + vir_end)
            runner = CliRunner()
            result = runner.invoke(cmd_line.main, [
                'check', 'clamscan', '--notifier', 'loginfo',
                '--target', vfile])
        finally:
            os.remove(vfile)

        self.assertEqual(result.exit_code, 1)

    def test_clamscan_no_hit(self):  # pylint: disable=no-self-use
        "Test clamscan with no hit."

        vfile = os.path.abspath(os.path.dirname(configs.__file__))
        runner = CliRunner()
        result = runner.invoke(cmd_line.main, [
            'check', 'clamscan', '--notifier', 'loginfo',
            '--target', vfile])
        self.assertEqual(result.exit_code, 0)

    def test_catch_exception(self):  # pylint: disable=no-self-use
        """Simple test of an exception in processing.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_line.main, [
            'check', 'apt', '--notifier', 'loginfo', '--notifier', 'echo',
            '--age-in-days ff'])
        self.assertEqual(result.exit_code, 2)

        runner = CliRunner()
        result = runner.invoke(cmd_line.main, [
            'check', 'apt', '--notifier', 'loginfo', '--notifier', 'echo',
            '--age-in-days', '-2'])
        self.assertEqual(result.exit_code, 2)
        self.assertEqual(
            result.output.split('\n')[:3], [
                'Error: ox_mon unexpected exception',
                'Error: ox_mon unexpected exception:',
                'Cannot have negative age_in_days: -2.0'])

    def test_file_checker_exists(self):  # pylint: disable=no-self-use
        "Test file checker existence test"

        junk_fd, tfile = tempfile.mkstemp()
        os.close(junk_fd)
        runner = CliRunner()
        result = runner.invoke(cmd_line.main, [
            'check', 'filestatus', '--target', tfile, '--live'])
        self.assertEqual(result.exit_code, 0)

        result = runner.invoke(cmd_line.main, [
            'check', 'filestatus', '--target', tfile, '--dead'])
        self.assertTrue(result.exit_code)
        os.remove(tfile)

        self.assertFalse(os.path.exists(tfile))
        result = runner.invoke(cmd_line.main, [
            'check', 'filestatus', '--target', tfile])
        self.assertEqual(result.exit_code, 0)

        result = runner.invoke(cmd_line.main, [
            'check', 'filestatus', '--target', tfile, '--dead'])
        self.assertEqual(result.exit_code, 0)

    def test_version_checker(self):  # pylint: disable=no-self-use
        "Test verison checker"

        runner = CliRunner()
        result = runner.invoke(cmd_line.main, [
            'check', 'vcmp', '--exact', '1.20.3', '--cmd', sys.executable,
            '--flags', ':c,print("version 1.20.3")'])
        self.assertEqual(result.exit_code, 0)

        result = runner.invoke(cmd_line.main, [
            'check', 'vcmp', '--exact', '1.20.4', '--cmd', sys.executable,
            '--flags', ':c,print("version 1.20.3")'])
        self.assertTrue(result.exit_code)

        result = runner.invoke(cmd_line.main, [
            'check', 'vcmp', '--minv', '1.20.4', '--cmd', sys.executable,
            '--flags', ':c,print("version 1.20.3")'])
        self.assertTrue(result.exit_code)

        result = runner.invoke(cmd_line.main, [
            'check', 'vcmp', '--minv', '1.20.2', '--cmd', sys.executable,
            '--flags', ':c,print("version 1.20.3")'])
        self.assertFalse(result.exit_code)

        result = runner.invoke(cmd_line.main, [
            'check', 'vcmp', '--minv', '1.20.13', '--cmd', sys.executable,
            '--flags', ':c,print("version 1.20.13")'])
        self.assertFalse(result.exit_code)

        result = runner.invoke(cmd_line.main, [
            'check', 'vcmp', '--maxv', '1.20', '--cmd', sys.executable,
            '--flags', ':c,print("version 1.20")'])
        self.assertFalse(result.exit_code)

        result = runner.invoke(cmd_line.main, [
            'check', 'vcmp', '--maxv', '1.20.4', '--cmd', sys.executable,
            '--flags', ':c,print("version 1.20.3")'])
        self.assertFalse(result.exit_code)

        result = runner.invoke(cmd_line.main, [
            'check', 'vcmp', '--maxv', '1.20.2', '--cmd', sys.executable,
            '--flags', ':c,print("version 1.20.3")'])
        self.assertTrue(result.exit_code)

        result = runner.invoke(cmd_line.main, [
            'check', 'vcmp', '--maxv', '1.20.2', '--cmd', sys.executable,
            '--vre', 'VeRsio',
            '--flags', ':c,print("VeRsio 1.20.3")'])
        self.assertTrue(result.exit_code)

    def test_raw_cmd(self):  # pylint: disable=no-self-use
        "Test raw cmd"

        runner = CliRunner()
        result = runner.invoke(cmd_line.main, [
            'gcmd', 'raw', '--cmd', 'test', '--args',
            '1,==,0'])
        self.assertTrue(result.exit_code)

    def test_raw_cmd_more(self):  # pylint: disable=no-self-use
        "Provide additional tests for raw_cmd which are more complicated."

        tfile = tempfile.mktemp()  # need since tester confuses stdout
        efile = tempfile.mktemp()  # need since tester confuses stdout
        runner = CliRunner()
        result = runner.invoke(cmd_line.main, [
            'gcmd', 'raw', '--cmd', 'test', '--args',
            '1,==,1', '--stderr', efile, '--stdout', tfile])
        os.remove(tfile)
        os.remove(efile)
        self.assertFalse(result.exit_code)


if __name__ == '__main__':
    unittest.main()

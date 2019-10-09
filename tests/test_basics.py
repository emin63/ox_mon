"""Some simple basic tests for ox_mon.
"""

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
        my_config = configs.BasicConfig(age_in_days=1e100000,
                                        notifier=['loginfo'])
        chk = apt_checker.AptShellChecker(my_config)
        data = chk.check()
        self.assertEqual(data, 'No packages need updating.')

    def test_apt_via_cmdline(self):  # pylint: disable=no-self-use
        """Simple test of basic apt shell checker using click CLI runner
        """
        runner = CliRunner()
        result = runner.invoke(cmd_line.main, [
            'check', 'apt', '--notifier', 'loginfo', '--notifier', 'echo'])
        self.assertEqual(result.exit_code, 0)

    def test_apt_force_notify(self):  # pylint: disable=no-self-use
        """Simple test of basic apt shell checker to force notification.

        This is helpful because it verifies at least basic notifiers work.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_line.main, [  # use age 0 to force notify
            'check', 'apt', '--notifier', 'echo', '--age-in-days', '0'])
        self.assertEqual(result.exit_code, 1)

    def disk_checker(self, max_pct):  # pylint: disable=no-self-use
        """Simple test of basic disk checker.
        """
        runner = CliRunner()
        result = runner.invoke(cmd_line.main, [
            'check', 'disk', '--notifier', 'loginfo',
            '--max-used-pct', max_pct])
        return result

    def test_disk_checker(self):  # pylint: disable=no-self-use
        "Test disk checker success and failure."
        proc = self.disk_checker('99')
        self.assertEqual(proc.exit_code, 0)
        proc = self.disk_checker('0')
        self.assertEqual(proc.exit_code, 1)

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


if __name__ == '__main__':
    unittest.main()

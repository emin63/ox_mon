"""Module for checking disk status.
"""

import logging
import shutil

from ox_mon.common import exceptions, configs, interface


class DiskUseTooHigh(exceptions.OxMonAlarm):
    """Exception for when disk usage is too high.
    """

    def __init__(self, loc: str, cur_pct_use: float, max_pct_use: float,
                 *args, **kwargs):
        msg = "Disk usage for %s too high: %.2f%% > %.2f%%" % (
            loc, cur_pct_use, max_pct_use)
        super().__init__(msg, *args, **kwargs)


class SimpleDiskChecker(interface.Checker):
    """Checker for testing disk usage.
    """

    @classmethod
    def options(cls):
        logging.debug('Making options for %s', cls)
        result = configs.BASIC_OPTIONS + [
            configs.OxMonOption(
                'tool', default='shutil', help=(
                    'Tool to use to determine disk usage. Default is '
                    'shutil which is sometimes flaky. If you install '
                    'psutil you can provide psutil for better results.')),
            configs.OxMonOption(
                'target', default='/', help=(
                    'Target location to check for usage (e.g., /).')),
            configs.OxMonOption(
                'max-used-pct', default=85.0, type=float, help=(
                    'Maximum percentage allowed for disk usage.'))
            ]
        return result

    def _get_du(self):
        "Get disk usage based on desired tool."

        if self.config.tool == 'shutil':
            result = shutil.disk_usage(self.config.target)
        elif self.config.tool == 'psutil':
            # pylint: disable=import-outside-toplevel
            import psutil
            result = psutil.disk_usage(self.config.target)
        else:
            raise ValueError('Invalid tool "%s"' % self.config.tool)
        return result

    def _check(self):
        """Check disk usage.
        """

        disk_usage = self._get_du()
        current_percent_usage = (
            disk_usage.used/disk_usage.total) * 100

        if current_percent_usage > self.config.max_used_pct:
            raise DiskUseTooHigh(
                self.config.target,
                current_percent_usage, self.config.max_used_pct)

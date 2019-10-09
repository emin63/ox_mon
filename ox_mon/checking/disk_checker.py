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
                'max-used-pct', default=85.0, type=float, help=(
                    'Maximum percentage allowed for disk usage.'))
            ]
        return result

    def _check(self):
        """Check disk usage.
        """

        loc = "/"
        disk_usage = shutil.disk_usage(loc)
        current_percent_usage = (disk_usage.used/disk_usage.free) * 100

        if current_percent_usage > self.config.max_used_pct:
            raise DiskUseTooHigh(
                loc, current_percent_usage, self.config.max_used_pct)

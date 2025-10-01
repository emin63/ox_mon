"""Module for checking file status.
"""

import glob
import time
import os
import logging

from ox_mon.common import exceptions, configs, interface


class UnexpectedFileStatus(exceptions.OxMonAlarm):
    """Exception to indicate something was incorrect with file status.
    """


class SimpleFileChecker(interface.Checker):
    """Checker for file status (existence, non-existence, age, etc.)
    """

    @classmethod
    def options(cls):
        logging.debug('Making options for %s', cls)
        result = configs.BASIC_OPTIONS + [
            configs.OxMonOption(
                'target', multiple=True, default=(), help=(
                    'Path to target file to check; can specify more than once.')),
            configs.OxMonOption(
                '--globtarget', multiple=True, default=(), help=(
                    'Like target but will apply glob pattern matching.')),
            configs.OxMonOption(
                '--live', default=False, type=bool, is_flag=1, help=(
                    'If this option is given then file must exist.')),
            configs.OxMonOption(
                '--dead', default=False, type=bool, is_flag=1, help=(
                    'If this option is given then file must not exist.')),
            configs.OxMonOption(
                '--min_size_kb', type=float, help=(
                    'If given then file must be at least this many kilobytes.')),
            configs.OxMonOption(
                '--max-age-in-hours', type=float, help=(
                    'If given and file exists and is older then alarm raised.'
                    )),
            configs.OxMonOption(
                '--max-age-in-days', type=float, help=(
                    'If given and file exists and is older then alarm raised.'
                    ))
            ]
        return result

    def _check_liveness(self, target):
        """Check if existence correct.
        """
        if self.config.live:
            if not os.path.exists(target):
                msg = 'Required file does not exist: %s' % target
                raise UnexpectedFileStatus(msg)
        if self.config.dead:
            if os.path.exists(target):
                msg = 'Forbidden file present: %s' % target
                raise UnexpectedFileStatus(msg)

    def _check_age(self, target):
        """Check if file age is reasonable.
        """
        if not os.path.exists(target):
            return  # File does not exist so cannot check max age items
        stat_info = None
        if self.config.max_age_in_hours is not None:
            stat_info = os.stat(target)
            self._check_max_age_hours(stat_info, target)
        if self.config.max_age_in_days is not None:
            stat_info = stat_info if stat_info else os.stat(target)
            self._check_max_age_days(stat_info, target)
        return stat_info

    def _check_max_age_hours(self, stat_info, target):
        """Take result of scan system call and check age in hours.

Should be called by _check method an dnot directly.
        """
        age_in_seconds = time.time() - stat_info.st_mtime
        age_in_hours = age_in_seconds / 3600.0
        if age_in_hours > self.config.max_age_in_hours:
            msg = 'File age %.2f hours > %.2f hours: %s' % (
                age_in_hours, self.config.max_age_in_hours, target)
            raise UnexpectedFileStatus(msg)

    def _check_max_age_days(self, stat_info, target):
        """Take result of scan system call and check age in days.

Should be called by _check method an dnot directly.
        """
        age_in_seconds = time.time() - stat_info.st_mtime
        age_in_days = age_in_seconds / 86400.0
        if age_in_days > self.config.max_age_in_days:
            msg = 'File age %.2f days > %.2f days: %s' % (
                age_in_days, self.config.max_age_in_days, target)
            raise UnexpectedFileStatus(msg)

    def _check_size(self, stat_info, target):
        """Take result of scan system call and check size.
        """
        min_size_kb = getattr(self.config, 'min_size_kb', None)
        if min_size_kb:
            stat_info = stat_info if stat_info else os.stat(target)
            size_kb = stat_info.st_size/1000.0
            if size_kb < min_size_kb:
                msg = (f'File size {size_kb:.3f} KB <'
                       f' {min_size_kb:2} KB: {target}')
                raise UnexpectedFileStatus(msg)

    def _check(self):
        """Check file liveness, age, etc.
        """
        files_to_check = list(self.config.target)
        for globtarget in self.config.globtarget:
            glob_hits = glob.glob(globtarget)
            if not glob_hits:
                raise UnexpectedFileStatus(f'No hits for globtarget {globtarget}')
            files_to_check.extend(glob_hits)
        for target in files_to_check:
            self._check_liveness(target)
            stat_info = self._check_age(target)
            self._check_size(stat_info, target)

        return 'Status as expected.'

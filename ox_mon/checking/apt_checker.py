"""Module for checking things using shell commands.

"""

import socket
import logging
import time
import os
import re
import subprocess
import typing

from ox_mon.common import exceptions
from ox_mon.common import configs
from ox_mon.common import interface


class GenericPackageInfo:
    """Generic information about a package.
    """

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    def __str__(self):
        return '%s: %s' % (self.name, self.version)


class NeedAptUpdate(exceptions.OxMonAlarm):
    """Exception for when apt update has not been run recently enough.
    """

    def __init__(self, fname, age_in_days, req_age_in_days, *args, **kwargs):
        msg = 'Apt file has age of %.1f days > required %.1f days: %s' % (
            age_in_days, req_age_in_days, fname)
        super().__init__(msg, *args, **kwargs)


class PackagesNeedUpdating(exceptions.OxMonAlarm):
    """Exception for when an apt package needs updating.
    """

    def __init__(self, pkg_info, *args, **kwargs):
        msg = self.make_msg(pkg_info)
        super().__init__(msg, *args, **kwargs)

    @classmethod
    def make_msg(cls, pkg_info: typing.List[GenericPackageInfo]) -> str:
        """Make message describing problem.

        :param pkg_info:     List of GenericPackageInfo instances which
                             need updating.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        :return:  String describing problem.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:  Create message describing problem.

        """
        details = cls.make_details()
        msg = 'Found %i uninstalled packges:\n%s\n--------------\n%s' % (
            len(pkg_info), '\n'.join([str(item) for item in pkg_info]),
            details)
        return msg

    @staticmethod
    def make_details() -> typing.Dict[str, str]:
        """Make dictionary of details for current system.
        """
        data = {
            'uname': str(os.uname()),
            'hostname': socket.gethostname(),
            }
        data['ip'] = socket.gethostbyname(data['hostname'])
        return data


class AptChecker(interface.Checker):
    """Basic checker class for apt updates.

This is an abstract class which you must-subclass. The main method in
this class is the `_check` method which checks if there are pending
security updates in the apt package manager` to install and notifies
based on this.

    """

    @classmethod
    def options(cls):
        logging.debug('Making options for %s', cls)
        result = configs.BASIC_OPTIONS + [
            configs.OxMonOption('age-in-days', default=7.0, type=float, help=(
                'Max age in days allowed since last update of apt sources')),
            configs.OxMonOption('limit', default=0, type=int, help=(
                'Max allowed un-installed packages to allow. Default is 0 '
                'so that any un-installed packages cause an alarm.'))
            ]
        return result

    def check_repo_updated_recently(self):
        """Check if the package repository has been updated recently.

Should use self.config.age_in_days. Sub-classes must implement.
        """
        raise NotImplementedError

    def check_updates(self):
        """Check if there are packages we need to update.

Sub-classes must implement.
        """
        raise NotImplementedError

    def filter_security_updates(self, update_info) -> typing.List[
            GenericPackageInfo]:
        """Take result of check_updates and filter to security updates.

Returns a list of GenericPackageInfo representing pending security updates.
        """
        raise NotImplementedError

    def _check(self):
        """Check if there are security packages to update.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:   Check if there are security packages to update.
                   If so, notify based on self.config.notifiers.

        """
        self.check_repo_updated_recently()
        update_info = self.check_updates()
        pkg_info = self.filter_security_updates(update_info)

        if pkg_info and len(pkg_info) > self.config.limit:
            raise PackagesNeedUpdating(pkg_info)

        return 'No packages need updating.'


class AptShellChecker(AptChecker):
    """Version of apt checker using shell commands.
    """

    sec_re = re.compile('^Inst.*securi')
    update_success_file = '/var/lib/apt/periodic/update-success-stamp'

    def filter_security_updates(self, update_info):
        result = []
        lines = update_info.stdout.decode('utf8').split('\n')
        for item in lines:
            if not self.sec_re.match(item):
                logging.debug('"%s" since not security update; skip', item)
                continue
            sitem = item.split(' ')
            result.append(GenericPackageInfo(
                sitem[1], sitem[2].lstrip('[').rstrip(']')))
        return result

    def check_repo_updated_recently(self):
        if self.config.age_in_days < 0:
            raise ValueError('Cannot have negative age_in_days: %s' % (
                self.config.age_in_days))
        if not os.path.exists(self.update_success_file):
            msg = '\n'.join([
                'Could not find file %s.' % self.update_success_file,
                'Have you done "apt install update-notifier-common" and'
                'also "apt update"? The update-notifier-common package'
                'is necessary to update the file %s' % (
                    self.update_success_file)])
            raise ValueError(msg)
        info = os.stat(self.update_success_file)
        age_in_seconds = time.time() - info.st_mtime
        age_in_days = age_in_seconds / 86400.0
        if age_in_days > float(self.config.age_in_days):
            raise NeedAptUpdate(self.update_success_file, age_in_days,
                                self.config.age_in_days)

    def check_updates(self):

        cmd = ['apt-get', '-s', 'dist-upgrade']
        proc = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
        return proc

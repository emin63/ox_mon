"""Module for checking versions of things.
"""

import re
import subprocess
import logging

from ox_mon.common import exceptions, configs, interface


class UnexpectedVersion(exceptions.OxMonAlarm):
    """Exception to indicate version was wrong.
    """


class SimpleVersionChecker(interface.Checker):
    """Checker for versions of things.
    """

    @classmethod
    def options(cls):
        logging.debug('Making options for %s', cls)
        result = configs.BASIC_OPTIONS + [
            configs.OxMonOption(
                '--cmd', help=('Command to run to generate version')),
            configs.OxMonOption(
                '--flags', default='::version', help=(
                    'Comma separated list of options to pass to --cmd. '
                    'We replace colons with dashes so e.g., :v becomes -v.')),
            configs.OxMonOption(
                '--vre', default='[0-9]+[.][0-9]+[.]?[0-9]*', help=(
                    'Regular expression to find version in --cmd output.'
                    )),
            configs.OxMonOption('--exact', default=None, help=(
                'If provided, version must exactly match this.')),
            configs.OxMonOption('--cmpmode', default='int', help=(
                'If "str" compare as strings. If int compare as integers. '
                'In either case, first we split on the "." character.')),
            configs.OxMonOption('--minv', default=None, help=(
                'If given then this is minimum allowed version with '
                'comparison done based on --cmpmode.')),
            configs.OxMonOption('--maxv', default=None, help=(
                'If given then this is maximum allowed version with '
                'comparison done based on --cmpmode.')),
            ]
        return result

    def _get_version(self, cmd_out: str):
        """Find and return version string from command output.
        """
        my_re = re.compile(self.config.vre)
        match = my_re.search(cmd_out)
        return match

    def _compare_version(self, version):
        if self.config.exact is not None:
            if self.config.exact != version:
                raise UnexpectedVersion(
                    'Expected version "%s" but got "%s"' % (
                        self.config.exact, version))

        if self.config.minv:
            split_version = version.split('.')
            minv = self.config.minv.split('.')
            if self.config.cmpmode == 'int':
                minv = list(map(int, minv))
                split_version = list(map(int, split_version))
            elif self.config.cmpmode != 'str':
                raise ValueError('Invalid value for cmpmode: "%s"' % (
                    self.config.cmpmode))
            if split_version < minv:
                raise UnexpectedVersion('Version "%s" < minimum "%s"' % (
                    version, self.config.minv))
        if self.config.maxv:
            split_version = version.split('.')
            maxv = self.config.maxv.split('.')
            if self.config.cmpmode == 'int':
                maxv = list(map(int, maxv))
                split_version = list(map(int, split_version))
            elif self.config.cmpmode != 'str':
                raise ValueError('Invalid value for cmpmode: "%s"' % (
                    self.config.cmpmode))
            if split_version > maxv:
                raise UnexpectedVersion('Version "%s" > maximum "%s"' % (
                    version, self.config.maxv))

    def _check(self):
        """Check file liveness, age, etc.
        """
        cmd = [self.config.cmd]
        for item in self.config.flags.split(','):
            cmd.append(item.replace(':', '-'))
        proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        if proc.returncode != 0:
            stdout = proc.stdout.decode('utf8')
            stderr = proc.stderr.decode('utf8')

            raise ValueError('Bad return code %s from %s:\n%s' % (
                proc.returncode, cmd, (
                    stdout if stdout else '') + '\n' + (
                        stderr if stderr else '')))

        # Need to use getattr to avoid strange pytype errors in lines below
        cmd_out = getattr(proc, 'stdout', None)
        cmd_out = cmd_out if cmd_out else getattr(
            proc, 'stderr', None)

        match = self._get_version(cmd_out.decode('utf8'))
        if not match:
            raise ValueError(
                'Unable to extract version via regexp "%s" from "%s"' % (
                    self.config.vre, cmd_out))
        self._compare_version(match.group())
        return True

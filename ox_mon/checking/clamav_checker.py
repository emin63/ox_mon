"""Module for checking ClamAV using shell commands.

"""

import re
import logging
import os
import subprocess
import tempfile

import click

from ox_mon.common import configs, interface, exceptions


class InfectedFilesFound(exceptions.OxMonAlarm):
    "Exception to indicated infected files found."

    def __init__(self, scanned, infected, summary, *args, **kwargs):
        msg = 'Found %i / %i infected files in clamscan:\n%ssummary' % (
            infected, scanned, summary)
        super().__init__(msg, *args, **kwargs)


class ClamScanShellChecker(interface.Checker):
    """Version of clamscan checker using shell commands.
    """

    @classmethod
    def options(cls):
        "Override to provide options for ClamScanShellChecker."
        logging.debug('Making options for %s', cls)
        result = configs.BASIC_OPTIONS + [
            configs.OxMonOption(
                'target', type=click.Path(exists=True), help=(
                    'Path to target file or directory to scan.')),
            configs.OxMonOption(
                'clamopts', default=':r', help=(
                    'Comma separated list of options for clamscan. '
                    'We replace colons with dashes so e.g., :r becomes -r.'))
            ]
        return result

    @staticmethod
    def _parse_log(fname):
        text = open(fname).read()
        my_re = re.compile(
            r'-+ +SCAN SUMMARY +-+.*' +
            r'(?P<scanned>Scanned files:[^\n]+)\n' +
            r'(?P<infected>Infected files:[^\n]+)\n' +
            r'.*Time: .*\n*$', re.MULTILINE | re.DOTALL)
        match = my_re.search(text)
        if not match:
            raise ValueError('Could not parse clamscan results: ...%s\n' % (
                text[-300:]))
        summary = text[match.start():match.end()]
        scanned = int(match.group('scanned').split(' ')[-1])
        infected = int(match.group('infected').split(' ')[-1])
        return scanned, infected, summary

    def _check(self):
        "Check for viruses as required by parent class."

        try:
            my_fd, log = tempfile.mkstemp(suffix='_clamscan.txt')
            os.close(my_fd)
            cmd = ['clamscan', '--log=%s' % log, self.config.target]
            if self.config.clamopts:
                for item in self.config.clamopts.split(','):
                    cmd.append(item.replace(':', '-'))
            proc = subprocess.run(cmd, check=False)
            if not os.path.exists(log):
                raise ValueError('Could not find clamscan log at %s' % log)
            scanned, infected, summary = self._parse_log(log)
            if infected:
                raise InfectedFilesFound(scanned, infected, summary)
            if proc.returncode != 0:
                raise ValueError('Bad return code %s from clamscan:\n%s' % (
                    proc.returncode, summary))
            return 'No infected files from clamscan:\n%s' % summary
        finally:
            if os.path.exists(log):
                os.remove(log)

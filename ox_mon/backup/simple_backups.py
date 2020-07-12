"""Simple backups.
"""

import logging
import subprocess
import click
from ox_mon.common import configs, interface


class OxMonRsyncBackup(interface.OxMonTask):
    """Class to do simple backups using rsyc.
    """

    @classmethod
    def options(cls):
        "Override to provide options for OxMonBackup"

        result = configs.BASIC_OPTIONS + [
            configs.OxMonOption(
                'tool', default='rsync', help=(
                    'Tool to use to do the backup. Default is '
                    'rsync.')),
            configs.OxMonOption(
                'source', type=click.Path(exists=True), help=(
                    'Path to location to backup.')),
            configs.OxMonOption(
                'dest', type=click.Path(exists=False), help=(
                    'Path to location store backup.')),
            configs.OxMonOption(
                'opts', default=':av,::delete', help=(
                    'Comma separated list of options for tool. We replace '
                    'colons with dashes so e.g., :av becomes -av.')),
            ]
        return result

    def _do_task(self):
        "Override to do the actual backup"

        cmd = [self.config.tool]
        if self.config.opts:
            for item in self.config.opts.split(','):
                cmd.append(item.replace(':', '-'))
        cmd.append(self.config.source)
        cmd.append(self.config.dest)
        logging.debug('Using cmd: %s', str(cmd))
        proc = subprocess.run(cmd, check=False)
        if proc.returncode != 0:
            raise ValueError('Bad return code %s from %s' % (
                proc.returncode, self.config.tool))
        return 'Backup completed.'

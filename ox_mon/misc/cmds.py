"""Tasks which are really commands.
"""

import logging
import subprocess

from ox_mon.common import configs, interface


class RawCmd(interface.OxMonTask):
    """Raw command with benefits of ox_mon notifiers, etc.

This command is helpful in case you want to run a shell script
or other basic command and use ox_mon to verify that it ran correclty
with notifications sent if there are problems.
    """

    @classmethod
    def options(cls):
        logging.debug('Making options for %s', cls)
        result = configs.BASIC_OPTIONS + [
            configs.OxMonOption(
                '--cmd', help=('Command to run.')),
            configs.OxMonOption(
                '--flags', default='', help=(
                    'Comma separated list of options to pass to --cmd. '
                    'We replace colons with dashes so e.g., :v becomes -v.')),
            configs.OxMonOption(
                '--shell', default=False, help=(
                    'Whether to run --cmd through the shell.')),
            ]
        return result

    def _do_sub_cmd(self):
        if not self.config.cmd:
            raise ValueError('No value provided for --cmd.')
        cmd = [self.config.cmd]
        for item in self.config.flags.split(','):
            cmd.append(item.replace(':', '-'))
        proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              shell=self.config.shell)
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

        return True

    def _do_task(self):
        return self._do_sub_cmd()

"""Tasks which are really commands.
"""

import sys
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
                '--args', default='', help=(
                    'Comma separated list of args to pass to --cmd. '
                    'We replace colons with dashes so e.g., :v becomes -v.')),
            configs.OxMonOption(
                '--stdout', default='@STDOUT', help=(
                    'Where to send stdout of the underling command. '
                    'If you provide @STDOUT then the output from --cmd '
                    'will go on the standard output stream. You can also '
                    'provide @STDERR or path to a file or @NULL.')),
            configs.OxMonOption(
                '--stderr', default='@STDERR', help=(
                    'Where to send stderr of the underling command. '
                    'If you provide @STDERR then the output from --cmd '
                    'will go on the standard error stream. You can also '
                    'provide @STDERR or path to a file or @NULL.')),
            configs.OxMonOption(
                '--shell', default=False, help=(
                    'Whether to run --cmd through the shell.')),
            ]
        return result

    @staticmethod
    def _make_out_stream(place: str):
        """Make an output stream from string description.

        :param place:   String which is either path to a file, @STDOUT,
                        @STDERR, or @NULL.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        :return:   What should be passed to subprocess.run to make the
                   output go to desired stream.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:   Prepare output stream for subprocess.run

        """
        if place == '@STDOUT':
            return sys.stdout
        if place == '@STDERR':
            return sys.stderr
        if place == '@NULL':
            return subprocess.PIPE
        result = open(place, 'w+')  # w+ means we can read it as well
        return result

    @staticmethod
    def _pull_data_from_stream(stream) -> str:
        """Helper to pull data from a stream or string and return string.
        """
        if hasattr(stream, 'read'):
            stream.seek(0)
            output = stream.read()
        else:
            output = stream
        if hasattr(output, 'decode'):
            output = output.decode('utf8')
        return output or ''
        
    def _do_sub_cmd(self):
        if not self.config.cmd:
            raise ValueError('No value provided for --cmd.')
        cmd = [self.config.cmd]
        for item in self.config.args.split(','):
            if item != '':
                cmd.append(item.replace(':', '-'))
        stdout = self._make_out_stream(self.config.stdout)
        stderr = self._make_out_stream(self.config.stderr)
        try:
            proc = subprocess.run(cmd, check=False, stdout=stdout,
                                  stderr=stderr, shell=self.config.shell)
            logging.debug('Return value for cmd "%s": %s',
                          cmd, proc.returncode)
            if proc.returncode != 0:
                raise ValueError('Bad return code %s from %s:\n%s' % (
                    proc.returncode, cmd, self._pull_data_from_stream(
                        proc.stdout or stdout) + '\n' +
                    self._pull_data_from_stream(proc.stderr or stderr)))

        finally:
            for item in [stdout, stderr]:
                if item not in [None, sys.stdout, sys.stderr] and hasattr(
                        item, 'close'):
                    item.close()

    def _do_task(self):
        return self._do_sub_cmd()

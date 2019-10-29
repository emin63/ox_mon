"""Command line interface to ox_mon.
"""

import traceback
import sys
import logging
import typing

import click

from ox_mon import VERSION
from ox_mon.common import configs, exceptions
from ox_mon.checking import (
    apt_checker, clamav_checker, disk_checker, file_checker,
    version_checker)


def prep_sentry(dsn):
    """Prepare sentry if a dsn is passed in.

We do an import inside this function so we do not try to import sentry
if no DSN is given (e.g., if sentry is not installed).
    """
    capture = {'name': 'unknown', 'func': logging.critical}

    # pytype gets confused by conditional imports so don't do them
    # if we are in type checking mode
    if not typing.TYPE_CHECKING:
        import sentry_sdk  # pylint: disable=import-error
        sentry_sdk.init(dsn)
        capture = {'name': 'sentry', 'func': sentry_sdk.capture_exception}
    return capture


@click.group()
def main():
    "Command line interface to ox_mon."


@main.group()
def check():
    "Checking commands."


def add_options(olist: typing.List[configs.OxMonOption]):
    """Add options to a click command

    :param olist:  List of OxMonOption values.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    :return:  A decorator function to apply to a click command.

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:  For all elements in olist decorator to put those
              into a click command.
    """
    def _add_options(func):
        "Make decorator to apply options to click command."
        for opt in reversed(olist):
            func = click.option('--' + opt.key.lstrip('-'), **opt.data)(func)
        return func
    return _add_options


def generic_command(checker_cls: typing.Callable, sentry: str,
                    loglevel: str, **kwargs):
    """

    :param checker_cls:    Sub-class of interface.Checker to make a Checker
                           instance.

    :param sentry:         String DSN for sentry or None if not using sentry.

    :param loglevel:       String loglevel (e.g., 'DEBUG', 'INFO', etc.)

    :param **kwargs:       Passed to configs.BasicConfig

    ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    PURPOSE:    Implement boilerplate for command line call of basic
                checker. Basically, we do the following.

         1. Setup logging based on loglevel.
         2. Prepare sentry if desired.
         3. Create BasicConfig instance from **kwargs.
         4. Create checker_cls instance using config.
         5. Run check method and if an exception is encountered, then
            capture with sentry if desired and return non-zero exit code.



    """
    root_logger = logging.getLogger('')
    root_logger.setLevel(getattr(logging, loglevel))
    capture = {'name': 'logging.critical', 'func': logging.critical}
    if sentry:
        capture = prep_sentry(sentry)
    try:
        config = configs.BasicConfig(sentry=sentry, **kwargs)
        checker = checker_cls(config)
        checker.check()
    except exceptions.OxMonAlarm as ox_alarm:
        capture['func'](ox_alarm)
        sys.exit(1)
    except Exception as problem:  # pylint: disable=broad-except
        msg = 'Got Problem: %s' % str(problem)
        if capture:
            msg += '\nWill try to report via %s' % (
                capture.get('name', 'unknown'))
        logging.error(msg)
        capture['func'](problem)
        print(traceback.format_exc())
        sys.exit(2)


@check.command()
@add_options(apt_checker.AptChecker.options())
def apt(sentry, **kwargs):
    "Check to see what needs to be updated via 'apt'."

    return generic_command(apt_checker.AptShellChecker, sentry, **kwargs)


@check.command()
@add_options(disk_checker.SimpleDiskChecker.options())
def disk(sentry, **kwargs):
    "Check to see what needs to be updated via 'apt'."

    return generic_command(disk_checker.SimpleDiskChecker, sentry, **kwargs)


@check.command()
@add_options(clamav_checker.ClamScanShellChecker.options())
def clamscan(sentry, **kwargs):
    "Check virus scan using clamscan."

    return generic_command(clamav_checker.ClamScanShellChecker,
                           sentry, **kwargs)


@check.command()
@add_options(file_checker.SimpleFileChecker.options())
def filestatus(sentry, **kwargs):
    "Check file status."

    return generic_command(file_checker.SimpleFileChecker,
                           sentry, **kwargs)


@check.command()
@add_options(version_checker.SimpleVersionChecker.options())
def vcmp(sentry, **kwargs):
    "Compare version of some other command"

    return generic_command(version_checker.SimpleVersionChecker,
                           sentry, **kwargs)


@main.command()
def version():
    "Show version of ox_mon."
    msg = 'ox_mon version: %s' % VERSION
    click.echo(msg)
    return msg

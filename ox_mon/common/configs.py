"""Common configuration information.
"""

import os

import click


class OxMonOption:
    """Option for running ox_mon
    """

    def __init__(self, key, **kwargs):
        self.key = key
        self.data = dict(kwargs)


BASIC_OPTIONS = [
    OxMonOption('--notifier', default=['echo'], multiple=True, help=(
        'Notifier(s) to use (e.g., echo or email or sentry). You can '
        'provide multiple versions of this if you want multiple '
        'notifiers (e.g., --notifier echo --notifier email). '
        'Some notifiers will need additional parameters such as '
        'the DSN (provided with --SENTRY) or email credentials.')),
    OxMonOption('--SENTRY', default=lambda: os.getenv('SENTRY_DSN'),
                help=('Optional Sentry DSN if you want error reporting '
                      'via sentry.')),
    OxMonOption(
        '--OX_MON_EMAIL_TO', default=None, envvar='OX_MON_EMAIL_TO', help=(
            'Dynamic option for email address to notify. '
            'Should be a comma separated group of email '
            'addresses (e.g., foo@examle.com or a@b.c,d@e.f).'
            'If not set, will lookup from environment.')),
    OxMonOption(
        '--OX_MON_EMAIL_FROM', default=None, envvar='OX_MON_EMAIL_FROM', help=(
            'Dynamic option for email address to notify from. '
            'If not set, will lookup from environment.')),
    OxMonOption('--OX_MON_GMAIL_PASSWD', default=None,
                envvar='OX_MON_GMAIL_PASSWD', help=(
                    'Dynamic option for gmail password. '
                    'If provided and email notifier is requested, will '
                    'use this to send email via gmail. '
                    'If not set, will lookup from environment.')),
    OxMonOption('--OX_MON_SES_PROFILE', envvar='OX_MON_SES_PROFILE',
                default=None, help=(
                    'Dynamic option for AWS SES profile for email. '
                    'If provided and email notifier is requested, will '
                    'use this to send email via AWS SES. '
                    'If not set, will lookup from environment.')),
    OxMonOption('--loglevel', default='INFO', type=click.Choice([
        'DEBUG', 'INFO', 'WARNING', 'CRITICAL', 'ERROR']), help=(
            'Root log level to use while running.')),
    ]


class BasicConfig:
    """Configuration object for ox_mon.
    """

    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

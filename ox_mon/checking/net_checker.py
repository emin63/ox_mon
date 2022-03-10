"""Module for checking network status.
"""

import logging

import requests
from ox_mon.common import exceptions, configs, interface


class UnexpectedStatusCode(exceptions.OxMonAlarm):
    """Exception to indicate unexpected status code
    """


class SimpleURLChecker(interface.Checker):
    """Checker for URL being alive.
    """

    @classmethod
    def options(cls):
        logging.debug('Making options for %s', cls)
        result = configs.BASIC_OPTIONS + [
            configs.OxMonOption(
                'target', help=('URL to check.')),
            configs.OxMonOption(
                'accept', default='200/202', type=str, help=(
                    'Slash separated HTTP status code to accept.'))
            ]
        return result

    def _do_request(self):
        """Do the URL request
        """
        response = requests.get(self.config.target)
        allowed = {int(i) for i in self.config.accept.split('/')}
        if response.status_code in allowed:
            return 'Received allowed status: %s' % str(
                response.status_code)
        raise UnexpectedStatusCode('Status %s not in %s; text:\n%s\n' % (
            response.status_code, allowed, getattr(
                response, 'text', '<unknown>')))

    def _check(self):
        """Check file liveness, age, etc.
        """
        return self._do_request()

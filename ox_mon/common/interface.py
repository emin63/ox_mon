"""Common interface for various types of monitors in ox_mon
"""


import datetime
import logging

from ox_mon.common import exceptions
from ox_mon.common import noters


class Checker:
    """Abstract class representing interface for Checker.

Each checker should implement the following interface:

  1. Have an `__init__` method that takes a config object.
  2. Have a _check method (see docs below).
  3. Have an options method (see docs below).

With those features implemented, it is easy to turn run checkers in
a consistent way by creating an instance and running the check method.
This can be done either using pure python or through the command line
as documented elsewhere.
    """

    def _check(self) -> str:
        """Main method to check system; raise OxMonAlarm if problem found.

This method should do whatever it needs to check the status of the system.
If everything is OK, it can return a string status message if desired or
just return None. If problems are found, this should raise an instance
of OxMonAlarm describing the problem.

That will be caught by the check method and a notification will be ent
to the appropriate place.

Users should call `check` which calls this method; do not call this
method directlry.
        """
        raise NotImplementedError

    @classmethod
    def options(cls):
        """Return list of configs.OxMonOption for configure this Checker.
        """
        raise NotImplementedError

    def __init__(self, config):
        self.config = config

    def notify(self, subject: str, msg: str):
        """Notify for given subject and message.

        :param subject:   String subject for notification.

        :param msg:       String message for notification.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        PURPOSE:  Go through all notifiers in self.config.notifiers and
                  send the given notification message.
        """
        for ntype in self.config.notifier:
            my_noter = noters.make_notifier(ntype, self.config)
            my_noter.send(subject, msg)

    def check(self):
        """Run the _check method with notification, etc.

        ~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

        """
        try:
            result = self._check()
            return result
        except exceptions.OxMonAlarm as ox_alarm:
            logging.info(
                'Raising ox_mon alarm: %s; will attempt to notify', ox_alarm)
            summary = 'ox_mon alarm for %s' % self.__class__.__name__
            self.notify(summary, '%s at UTC %s\n%s' % (
                summary, datetime.datetime.utcnow(), str(ox_alarm)))
            raise
        except exceptions.OxMonException as ox_prob:
            logging.warning(
                'Got ox_mon exception: %s; will attempt to notify', ox_prob)
            self.notify('Error: ox_mon failed',
                        'Error: ox_mon failed:\n%s' % str(ox_prob))
            raise
        except Exception as unexpected:
            logging.error(
                'Got unexpected exception %s; will attempt to notify', str(
                    unexpected))
            self.notify('Error: ox_mon unexpected exception',
                        'Error: ox_mon unexpected exception:\n%s' % str(
                            unexpected))
            raise

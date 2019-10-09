"""Exception information for ox_mon
"""


class OxMonException(Exception):
    """Base class for ox_mon exceptions to catch and report.
    """


class OxMonAlarm(OxMonException):
    """Base class for an alarm condition which should be reported.
    """

Introduction
============

The `ox\ :sub:`mon` <https://github.com/emin63/ox_mon>`__ package
provides some tools to keep your machine up to date.

Installation
============

You can install via the usual ``pip install ox_mon``. If you want to
install and be able to edit your installation, you may consider doing
something like ``pip install --editable ox_mon``.

Usage
=====

You can see the list of possible commands via

.. code:: bash

    ox_mon check --help

One of the most useful commands is ``ox_mon check``. This will check
your Ubuntu installation to see if you have the latest security updates
installed. If you do, then nothing happens. If you have not done
``apt update`` recently or you do **NOT** have the latest packages
installed, then you will be notified.

You can control the notification methods and how many days have passed
since you did ``apt update`` using command line options. For example,
doing

.. code:: bash

    ox_mon check --notifiers echo --age-in-days 7

would not notify you provided that you have done ``apt update`` within 7
days. If your packages are stale, the notification will just print a
message. See the `Notifiers section <id:sec-notifiers>`__ for
notification options.

Notifiers
---------

There are a variety of ways to get notifications:

-  ``echo``: Just echoes notification to stdout.
-  ``email``: Will send you an email provided you specify the following:

   -  ``OX_MON_EMAIL_TO``: A comma separated list of email addresses
      (e.g., ``foo@exmaple.com`` or ``foo@exmaple.com,bar@example.com``)
      to send email to. If not set, will attempt to lookup from
      environment variable.
   -  ``OX_MON_EMAIL_FROM``: Sending email address. If not set, will
      attempt to lookup from environment variable.
   -  ``OX_MON_GMAIL_PASSWD``: A password to use if you want to use
      gmail as the SMTP relay to send mail from. This password should
      correspond to the username in ``OX_MON_EMAIL_FROM``.
   -  ``OX_MON_SES_PROFILE``: If provided and email notifier is
      requested, will use this to send email via AWS SES. If not set,
      will attempt lookup from environment.
   -  **IMPORTANT**: Either ``OX_MON_SES_PROFILE`` or
      ``OX_MON_GMAIL_PASSWD`` is required to send emails.

-  ``loginfo``: Will use Python's ``logging.info`` to send notification.
   This can be useful if you do not want the notifications in stdout but
   in stderr.

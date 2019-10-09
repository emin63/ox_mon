Introduction
============

The `ox\_mon <https://github.com/emin63/ox_mon>`__ package provides some
tools to keep monitor your machine to keep it up to date, free of
viruses, and generally working properly.

Basically, there are lots of little monitoring and checking tasks you
may find yourself needing to do. You could write a separate script for
each such task, but it would be nice to have some basic scaffolding for
things like notifications, logging, testing, and so on to simplify
machine monitoring. Better yet, by having a common framework many
developers can contribute small snippets of such tools that work in a
similar way to simplify life for everyone.

Once you install ``ox_mon`` as described in the
`Installation <id:sec-installation>`__ section, you can do something
like

.. code:: bash

    ox_mon check <thing> [<OPTIONS]

to run various checks discussed in the `Checkers <id:sec-checkers>`__
section with a consistent reporting system described in the
`Notifiers <id:sec-notifiers>`__ section.

Installation
============

You can install via the usual ``pip install ox_mon``. If you want to
install and be able to edit your installation, you may consider doing
something like ``pip install --editable ox_mon``.

Usage
=====

You can see the list of possible commands via

.. code:: bash

    ox_mon --help

Checkers
--------

One of the most useful commands is ``ox_mon check``. If you try

.. code:: bash

    ox_mon check --help

you will see a list of possible checkers you can run. These all use the
same general syntax for things like how to notify an administrator if
issues are found while also checker specific customization.

Checker: apt
~~~~~~~~~~~~

The ``apt`` checker will check your Ubuntu installation to see if you
have the latest security updates installed. If you do, then nothing
happens. If you have not done ``apt update`` recently or you do **NOT**
have the latest security packages installed, then you will be notified.

You can control the notification methods and how many days have passed
since you did ``apt update`` using command line options. For example,
doing

.. code:: bash

    ox_mon check apt --notifier echo --age-in-days 7

would not notify you provided that you have done ``apt update`` within 7
days. If your packages are stale, the notification will just print a
message. See the `Notifiers section <id:sec-notifiers>`__ for
notification options.

Checker: disk
~~~~~~~~~~~~~

The ``disk`` checker will check your system to see if the disk is too
full. If so, you will be notified as described in the
`Notifiers <id:sec-notifiers>`__ section.

You can control the notification methods and how full the disk is
allowed to be before it triggers an alarm. For example, doing

.. code:: bash

    ox_mon check disk --notifier loginfo --max-used-pct 5

would not notify you using python's ``logging.INFO`` stream (which
usually goes to ``stderr``) if your disk is more than ``5%`` full.

Checker: anti-virus
~~~~~~~~~~~~~~~~~~~

The ``clamscan`` checker will use `ClamAV <https://www.clamav.net/>`__
(assuming you have it installed) to virus scan your system. You can
control the target location to scan via something like

.. code:: bash

    ox_mon check clamscan --target $HOME

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

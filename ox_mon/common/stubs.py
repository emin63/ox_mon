"""Stubs for various purposes.
"""

import doctest
import logging


class GenericModuleStub:
    """Generic stub for module we could not load.

Imagine that you need some module `fake_mod` for your program but only
for certain features. You want to import it and use it if that feature
is used, but not complain about import errors if the module is missing
and the feature is not used.

This class lets you create a generic module stub for that case as
illustrated below.

Basically, you catch the import error for importing your fake module,
then create a GenericModuleStub instance for the module:

>>> from ox_mon.common import stubs
>>> try:
...     import fake_mod
... except Exception as prob:
...     fake_mod = stubs.GenericModuleStub(
...         'fake_mod', str(prob), 'magical dependancies')
...
>>> try:  # show what would happen if you tried using fake_mod.bar
...     fake_mod.bar()
... except Exception as prob:
...     print(prob)
Unable to call method bar in module fake_mod.
Module fake_mod unimported because No module named 'fake_mod'.
If you want to use this feature; please install required
dependancies such as "magical dependancies"


You can also do fancier things to control exactly what happens for
certain stub method:


>>> from ox_mon.common import stubs
>>> try:
...     import fake_mod
... except Exception as prob:
...     fake_mod = stubs.GenericModuleStub(
...         'fake_mod', str(prob), 'magical dependancies')
...     fake_mod.test = fake_mod.make_complainer('test')  # stub method 'test'
...     fake_mod.foo = fake_mod.make_complainer('foo', note=(
...        'you can provide notes like: you really do not need foo anyway'))
...
>>> try:
...     fake_mod.test()
... except Exception as prob:
...     print(prob)
Unable to call method test in module fake_mod.
Module fake_mod unimported because No module named 'fake_mod'.
If you want to use this feature; please install required
dependancies such as "magical dependancies"


>>> try:
...     fake_mod.foo()
... except Exception as prob:
...     print(prob)
Unable to call method foo in module fake_mod.
Module fake_mod unimported because No module named 'fake_mod'.
If you want to use this feature; please install required
dependancies such as "magical dependancies"
you can provide notes like: you really do not need foo anyway

    """

    def __init__(self, modname, ierr, deps):
        """Initializer.

        :param modname:    String name of attempted module load.

        :param ierr:       String error in importing.

        :param deps:       String list of dependancies.

        """
        self.modname = modname
        self.ierr = ierr
        self.deps = deps

    def __getattr__(self, name):
        complainer = self.make_complainer(name)
        return complainer

    def complaint_msg(self, method: str, note: str = None) -> str:
        """Take in string method name and return complaint for it.
        """
        msg = '\n'.join([
            'Unable to call method %s in module %s.' % (method, self.modname),
            'Module %s unimported because %s.' % (self.modname, self.ierr),
            'If you want to use this feature; please install required',
            'dependancies such as "%s"' % self.deps] + (
                [note] if note else []))

        return msg

    def make_complainer(self, method_name: str, note: str = ''):
        """Take method name and return callable for it.

See class docs for example usage.
        """
        msg = self.complaint_msg(method_name, note)

        def complainer(*args, **kwargs):
            "Return function to complain if called."
            logging.debug('Ignoring *args=%s, **kwargs=%s for %s',
                          args, kwargs, method_name)
            raise ValueError(msg)
        return complainer


if __name__ == '__main__':
    doctest.testmod()
    print('Finished Tests')

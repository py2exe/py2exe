# py2exe/__init__.py

import sys
import py2exe
import distutils.command

__version__ = "0.1.2"

distutils.command.__all__.append('py2exe')

sys.modules['distutils.command.py2exe'] = py2exe


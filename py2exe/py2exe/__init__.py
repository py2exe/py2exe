# py2exe/__init__.py

import sys
import py2exe
import distutils.command

distutils.command.__all__.append('py2exe')

sys.modules['distutils.command.py2exe'] = py2exe


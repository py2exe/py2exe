"""
py2exe - build windows executables from Python scripts

TODO: This text will be displayed when 'help("py2exe")' is entered at the python prompt.
Write up a description of the options py2exe understands, for easy reference.
"""
# py2exe/__init__.py

# 'import py2exe' imports this package, and two magic things happen:
#
# - the 'py2exe.build_exe' submodule is imported and installed as
#   'distutils.commands.py2exe' command
#
# - the default distutils Distribution class is replaced by the
# special one contained in this module.
#

import distutils.dist, distutils.core, distutils.command, build_exe, sys

_KEYWORDS = "com_server service windows console zipfile".split()

class Distribution(distutils.dist.Distribution):

    def __init__(self, attrs):
        self.com_server = [] # com-servers to build
        self.service = []     # services to build
        self.windows = []    # gui apps to build
        self.console = []    # console apps to build
        self.zipfile = "library.zip" # zipfile containing the python modules needed by the above

        for name in _KEYWORDS:
            if attrs.has_key(name):
                setattr(self, name, attrs[name])
                del attrs[name]

        distutils.dist.Distribution.__init__(self, attrs)

distutils.core.Distribution = Distribution

distutils.command.__all__.append('py2exe')

sys.modules['distutils.command.py2exe'] = build_exe

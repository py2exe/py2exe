import distutils.dist, distutils.core, distutils.command, build_exe, sys

class Distribution(distutils.dist.Distribution):
    keywords = "com_dll com_exe service windows console dll".split()

    def __init__(self, attrs):
        self.com_dll = None
        self.com_exe = None
        self.service = None
        self.windows = None
        self.console = None
        self.dll = None

        for name in self.keywords:
            val = attrs.get(name, None)
            setattr(self, name, val or [])
            if val is not None:
                del attrs[name]

        distutils.dist.Distribution.__init__(self, attrs)

distutils.core.Distribution = Distribution

distutils.command.__all__.append('py2exe')

sys.modules['distutils.command.py2exe'] = build_exe


import distutils.dist, distutils.core, distutils.command, build_exe, sys

_KEYWORDS = "com_server service windows console".split()

class Distribution(distutils.dist.Distribution):

    def __init__(self, attrs):
        self.com_server = None
        self.service = None
        self.windows = None
        self.console = None

        for name in _KEYWORDS:
            val = attrs.get(name, None)
            setattr(self, name, val or [])
            if val is not None:
                del attrs[name]

        self.zipfile = attrs.get("zipfile", "library")
        try:
            del attrs["zipfile"]
        except KeyError:
            pass

        distutils.dist.Distribution.__init__(self, attrs)

distutils.core.Distribution = Distribution

distutils.command.__all__.append('py2exe')

sys.modules['distutils.command.py2exe'] = build_exe


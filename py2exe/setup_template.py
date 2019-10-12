#!/usr/bin/python3
# -*- coding: utf-8 -*-

from string import Template
import os, sys


HEADER = """\
#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Created by: $created_by

from distutils.core import setup
import py2exe

class Target(object):
    '''Target is the baseclass for all executables that are created.
    It defines properties that are shared by all of them.
    '''
    def __init__(self, **kw):
        self.__dict__.update(kw)

        # the VersionInfo resource, uncomment and fill in those items
        # that make sense:
        
        # The 'version' attribute MUST be defined, otherwise no versioninfo will be built:
        # self.version = "1.0"
        
        # self.company_name = "Company Name"
        # self.copyright = "Copyright Company Name © 2013"
        # self.legal_copyright = "Copyright Company Name © 2013"
        # self.legal_trademark = ""
        # self.product_version = "1.0.0.0"
        # self.product_name = "Product Name"

        # self.private_build = "foo"
        # self.special_build = "bar"

    def copy(self):
        return Target(**self.__dict__)

    def __setitem__(self, name, value):
        self.__dict__[name] = value

RT_BITMAP = 2
RT_MANIFEST = 24

# A manifest which specifies the executionlevel
# and windows common-controls library version 6

manifest_template = '''\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="*"
    name="%(prog)s"
    type="win32"
  />
  <description>%(prog)s</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel
            level="%(level)s"
            uiAccess="false">
        </requestedExecutionLevel>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="*"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
  </dependency>
</assembly>
'''

"""

TARGET = """
$myapp = Target(
    # We can extend or override the VersionInfo of the base class:
    # version = "1.0",
    # file_description = "File Description",
    # comments = "Some Comments",
    # internal_name = "spam",

    script="$script", # path of the main script

    # Allows to specify the basename of the executable, if different from '$myapp'
    # dest_base = "$myapp",

    # Icon resources:[(resource_id, path to .ico file), ...]
    # icon_resources=[(1, r"$myapp.ico")]

    other_resources = [(RT_MANIFEST, 1, (manifest_template % dict(prog="$myapp", level="asInvoker")).encode("utf-8")),
    # for bitmap resources, the first 14 bytes must be skipped when reading the file:
    #                    (RT_BITMAP, 1, open("bitmap.bmp", "rb").read()[14:]),
                      ]
    )
"""

OPTIONS = """
# ``bundle_files`` option explained:
# ===================================================
#
# The py2exe runtime *can* use extension module by directly importing
# the from a zip-archive - without the need to unpack them to the file
# system.  The bundle_files option specifies where the extension modules,
# the python dll itself, and other needed dlls are put.
#
# bundle_files == 3:
#     Extension modules, the Python dll and other needed dlls are
#     copied into the directory where the zipfile or the exe/dll files
#     are created, and loaded in the normal way.
#
# bundle_files == 2:
#     Extension modules are put into the library ziparchive and loaded
#     from it directly.
#     The Python dll and any other needed dlls are copied into the
#     directory where the zipfile or the exe/dll files are created,
#     and loaded in the normal way.
#
# bundle_files == 1:
#     Extension modules and the Python dll are put into the zipfile or
#     the exe/dll files, and everything is loaded without unpacking to
#     the file system.  This does not work for some dlls, so use with
#     caution.
#
# bundle_files == 0:
#     Extension modules, the Python dll, and other needed dlls are put
#     into the zipfile or the exe/dll files, and everything is loaded
#     without unpacking to the file system.  This does not work for
#     some dlls, so use with caution.


py2exe_options = dict(
    packages = [$packages],
##    excludes = "tof_specials Tkinter".split(),
##    ignores = "dotblas gnosis.xml.pickle.parsers._cexpat mx.DateTime".split(),
##    dll_excludes = "MSVCP90.dll mswsock.dll powrprof.dll".split(),
    optimize=$optimize,
    compressed=$compressed, # uncompressed may or may not have a faster startup
    bundle_files=$bundle_files,
    dist_dir=$destdir,
    )
"""

SETUP = """
# Some options can be overridden by command line options...

setup(name="name",
      # console based executables
      console=[$console],

      # windows subsystem executables (no console)
      windows=[$windows],

      # py2exe options
      options={"py2exe": py2exe_options},
      )
"""

def write_setup(args):
    with open(args.setup_path, "w", encoding="utf-8") as ofi:

        header = Template(HEADER)
        created_by = " ".join([os.path.basename(sys.executable), "-m", "py2exe"] + sys.argv[1:])
        print(header.substitute(locals()), file=ofi)
        console = []
        for target in args.script:
            script = target.script
            myapp = os.path.splitext(target.script)[0]
            target = Template(TARGET)
            print(target.substitute(locals()), file=ofi)
            console.append(myapp)

        console = ", ".join(console)
        windows = ""
        optimize = args.optimize or 0
        compressed = args.compress or False
        destdir = repr(args.destdir)

        packages = ", ".join(args.packages or [])
        bundle_files = args.bundle_files
        options = Template(OPTIONS)
        print(options.substitute(locals()), file=ofi)

        setup = Template(SETUP)
        print(setup.substitute(locals()), file=ofi)

    print("Created %s." % args.setup_path)

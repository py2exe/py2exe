import sys
import warnings

from setuptools import Command, dist

from . import runtime

def fancy_split(str, sep=","):
    # a split which also strips whitespace from the items
    # passing a list or tuple will return it unchanged
    if str is None:
        return []
    if hasattr(str, "split"):
        return [item.strip() for item in str.split(sep)]
    return str

def finalize_distribution_options(dist):
    if getattr(dist, "console", None) is None and getattr(dist, "windows", None) is None:
        return

    if getattr(dist.metadata, "py_modules", None) is None:
        dist.py_modules = []

    dist.console = runtime.fixup_targets(dist.console, "script")
    for target in dist.console:
        target.exe_type = "console_exe"

    dist.windows = runtime.fixup_targets(dist.windows, "script")
    for target in dist.windows:
        target.exe_type = "windows_exe"

    # name = getattr(dist.metadata, "name", None)
    # if name is None or name == "UNKNOWN":
    #     if dist.app:
    #         targets = fixup_targets(dist.app, "script")
    #     else:
    #         targets = fixup_targets(dist.plugin, "script")

    #     if not targets:
    #         return

    #     base = targets[0].get_dest_base()
    #     name = os.path.basename(base)

    #     dist.metadata.name = name

def validate_target(dist, attr, value):
    runtime.fixup_targets(value, "script")

def validate_zipfile(dist, attr, value):
    dist.zipfile = value

class py2exe(Command):
    description = ""
    # List of option tuples: long name, short name (None if no short
    # name), and help string.
    user_options = [
        ('optimize=', 'O',
         "optimization level: -O1 for \"python -O\", "
         "-O2 for \"python -OO\", and -O0 to disable [default: -O0]"),
        ('dist-dir=', 'd',
         "directory to put final built distributions in (default is dist)"),

        ("excludes=", 'e',
         "comma-separated list of modules to exclude"),
        ("dll-excludes=", None,
         "comma-separated list of DLLs to exclude"),
        ("ignores=", None,
         "comma-separated list of modules to ignore if they are not found"),
        ("includes=", 'i',
         "comma-separated list of modules to include"),
        ("packages=", 'p',
         "comma-separated list of packages to include"),

        ("compressed", 'c',
         "create a compressed zipfile"),

        ("xref", 'x',
         "create and show a module cross reference"),

        ("bundle-files=", 'b',
         "bundle dlls in the zipfile or the exe. Valid levels are 1, 2, or 3 (default)"),

        ("skip-archive", None,
         "do not place Python bytecode files in an archive, put them directly in the file system"),

        ("ascii", 'a',
         "do not automatically include encodings and codecs"),

        ('custom-boot-script=', None,
         "Python file that will be run when setting up the runtime environment"),

        ('use-assembly', None,
         "use windows assembly to isolate python dll in ctypes-com-server."),
        ]

    boolean_options = ["compressed", "xref", "ascii", "skip-archive","use-assembly"]

    def initialize_options (self):
        self.xref =0
        self.compressed = 0
        self.unbuffered = 0
        self.optimize = 0
        self.includes = None
        self.excludes = None
        self.ignores = None
        self.packages = None
        self.dist_dir = None
        self.dll_excludes = None
        self.typelibs = None
        self.bundle_files = 3
        self.skip_archive = 0
        self.ascii = 0
        self.custom_boot_script = None
        self.use_assembly = False

    def finalize_options (self):
        self.optimize = int(self.optimize)
        self.excludes = fancy_split(self.excludes)
        self.includes = fancy_split(self.includes)
        self.ignores = fancy_split(self.ignores)
        self.bundle_files = int(self.bundle_files)
        if self.bundle_files < 0 or self.bundle_files > 3:
            raise ValueError("bundle-files must be 0, 1, 2, or 3, not %s"
                             % self.bundle_files)
        if self.ascii:
            warnings.warn("The 'ascii' option is no longer supported, ignored.")
        if self.skip_archive:
            if self.compressed:
                raise ValueError("can't compress when skipping archive")
            if self.distribution.zipfile is None:
                raise ValueError("zipfile cannot be None when skipping archive")
        # includes is stronger than excludes
        for m in self.includes:
            if m in self.excludes:
                self.excludes.remove(m)
        self.packages = fancy_split(self.packages)
        self.set_undefined_options('bdist',
                                   ('dist_dir', 'dist_dir'))
        self.dll_excludes = [x.lower() for x in fancy_split(self.dll_excludes)]

    def run(self):
        build = self.reinitialize_command('build')
        build.run()
        sys_old_path = sys.path[:]
        try:
            ## if build.build_platlib is not None:
            ##     sys.path.insert(0, build.build_platlib)
            ## if build.build_lib is not None:
            ##     sys.path.insert(0, build.build_lib)
            self._run()
        ## except Exception:
        ##     import traceback; traceback.print_exc()
            # XXX need another way to report (?)
        finally:
            sys.path = sys_old_path

    def _run(self):
        dist = self.distribution

        ## # all of these contain module names
        ## required_modules = []
        ## for target in dist.com_server + dist.service + dist.ctypes_com_server:
        ##     required_modules.extend(target.modules)

        ## required_files = [target.script
        ##                   for target in dist.windows + dist.console]

        dist.console = runtime.fixup_targets(dist.console, "script")
        for target in dist.console:
            target.exe_type = "console_exe"

        dist.windows = runtime.fixup_targets(dist.windows, "script")
        for target in dist.windows:
            target.exe_type = "windows_exe"

##         # Convert our args into target objects.
##         dist.com_server = FixupTargets(dist.com_server, "modules")
##         dist.ctypes_com_server = FixupTargets(dist.ctypes_com_server, "modules")
##         dist.windows = FixupTargets(dist.windows, "script")
##         dist.console = FixupTargets(dist.console, "script")
##         dist.isapi = FixupTargets(dist.isapi, "script")

        from argparse import Namespace
        options = Namespace(xref = self.xref,
                            comppressed = self.compressed,
                            unbuffered = self.unbuffered,
                            optimize = self.optimize,
                            includes = self.includes,
                            excludes = self.excludes,
                            ignores = self.ignores,
                            packages = self.packages,
                            dist_dist = self.dist_dir,
                            dll_excludes = self.dll_excludes,
                            typelibs = self.typelibs,
                            bundle_files = self.bundle_files,
                            skip_archive = self.skip_archive,
                            ascii = self.ascii,
                            custom_boot_script = self.custom_boot_script,

                            script = dist.console + dist.windows,
                            #service = dist.service,
                            #com_servers = dist.ctypes_com_server,

                            destdir = self.dist_dir,
                            libname = dist.zipfile,

                            verbose = self.verbose,
                            report = False,
                            summary = False,
                            show_from = None,

                            data_files = self.distribution.data_files,

                            compress = self.compressed,
                            use_assembly = self.use_assembly,
                            )

        ## level = logging.INFO if options.verbose else logging.WARNING
        ## logging.basicConfig(level=level)
        #import pdb;pdb.set_trace()
        builder = runtime.Runtime(options)
        builder.analyze()
        builder.build()

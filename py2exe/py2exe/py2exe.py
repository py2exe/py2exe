"""distutils.command.py2exe

Implements the Distutils 'py2exe' command: create executable
windows programs from scripts."""

# created 2000/11/14, Thomas Heller

__revision__ = "$Id$"

__version__ = "0.2.0"

# ToDo:
#

import sys, os, string
from distutils.core import Command
from distutils.util import get_platform
from distutils.dir_util import create_tree, remove_tree
from distutils import file_util
from distutils.errors import *
from distutils.dep_util import newer
from distutils.spawn import spawn
import imp

_c_suffixes = ['.pyd', '.dll'] #+ ['_d.pyd', '_d.dll']

# The following issues have to be adressed:
# We (python) could be running in
#    1. debug mode - compiled python files have the extension .pyc
#    2. optimized mode (-O) - compiled python files have the extension .pyo
#    3. optimized mode (-OO) - compiled python files have the extension .pyo
#       and do not contain __doc__ strings
# We (python) could be running
#    4. the release binary of the python interpreter pythonxx.dll,
#       extension modules have the filenames <module>.pyd or <module>.dll
#    5. the debug binary of the python interpreter pythonxx.dll,
#       extension modules have the filenames <module>.pyd or <module>.dll
#
# in case 1, __debug__ is true, in cases 2 and 3 __debug__ is false.
# in case 4, imp.get_suffixes() returns something like [('.pyd',...), ('.dll',...), ...]
# in case 5, imp_get_suffixes() returns something like [('_d.pyd',...), ('_d.dll',...), ...]
#
# We should make it easy for us and simply refuse to build
# when running the debug python binary...

class py2exe (Command):

    description = "create executable windows programs from scripts"

    # XXX need more options: unbuffered, ???
    user_options = [
        ('debug', 'g',
         "create runtime with debugging information"),
        ('dist-dir=', 'd',
         "directory to put final built distributions in"),
        ('force', 'f', "force installation (overwrite existing files)"),
        ('keep-temp', 'k',
         "keep the pseudo-installation tree around after " +
         "creating the distribution archive"),
        ('optimize=', 'O',
         "optimization level: -O1 for \"python -O\", "
         "-O2 for \"python -OO\", and -O0 to disable [default: -O0]"),
        ('windows', 'w',
         "Create a Window application"),
        ('console', 'c',
         "Create a Console application"),
        ("excludes=", 'e',
         "comma-separated list of modules to exclude"),
        ("includes=", 'i',
         "comma-separated list of modules to include"),
        ]
    
    boolean_options = ['keep-temp', 'force', 'debug', 'windows', 'console']

    def initialize_options (self):
        self.bdist_dir = None
        self.dist_dir = None
        self.keep_temp = 0
        self.optimize = None
        self.force = 0
        self.debug = None
        self.windows = None
        self.console = None
        self.excludes = None
        self.includes = None

    # initialize_options()


    def finalize_options (self):
        if self.console and self.windows:
            raise DistutilsOptionError, \
                  "cannot select console and windows at the same time"
        if self.bdist_dir is None:
            bdist_base = self.get_finalized_command('bdist').bdist_base
            self.bdist_dir = os.path.join(bdist_base, 'winexe')

        self.set_undefined_options('bdist',
                                   ('dist_dir', 'dist_dir'))
        
        if self.optimize is None:
            self.optimize = 0

        if type(self.optimize) is not type(0):
            try:
                self.optimize = int(self.optimize)
                assert 0 <= self.optimize <= 2
            except (ValueError, AssertionError):
                raise DistutilsOptionError, "optimize must be 0, 1, or 2"

        if self.excludes:
            self.excludes = string.split(self.excludes, ',')
        else:
            self.excludes = []

        if self.includes:
            self.includes = string.split(self.includes, ',')
            # includes is stronger than excludes
            for m in self.includes:
                if m in self.excludes:
                    self.excludes.remove(m)
        else:
            self.includes = []

    # finalize_options()


    def run (self):
        if not self.distribution.scripts:
            # nothing to do
            # should raise an error!
            raise "Error", "Nothing to do"
            return

        # Distribute some of our options to other commands.
        # Is this the right way to do it?
        build_ext = self.reinitialize_command('build_ext')
        build_ext.force = self.force
        build_ext.debug = self.debug
        
        build = self.reinitialize_command('build')
        build.force = self.force

        install = self.reinitialize_command('install')
        install.force = self.force
        install.root = os.path.join(self.bdist_dir, "lib")
        install.optimize = install.compile = 0

        # build everything and do a fake install
        install.run()

        collect_dir = os.path.join(self.bdist_dir, "collect")
        self.mkpath(collect_dir)
        self.mkpath(self.dist_dir)

        extra_path = [os.path.abspath(os.path.normpath(install.install_lib))]

        # Problems with modulefinder:
        # Some extensions import python modules,
        # modulefinder cannot find them.
        # Examples: (from python 2.0)
        #   _sre imports copy_reg
        #   cPickle imports string, copy_reg
        #   cStringIO imports string
        #   parser imports copy_reg
        #   codecs imports encodings
        #
        # Update: The problem is even worse, because
        # cPickle imports string. copy_reg, types
        # with PyImport_ImportModule, which does not call the
        # import hook. So, we are not able the import them
        # from within the import of cPickle.
        #
        # Our solution:
        # Add them to the py_files we need, and additionally
        # 'import' them directly after installing the import hook.
        # We do this by collectiong them into the force_imports
        # list and writing an 'import ...' line to Scripts\support.py.
        import_hack = {
            "cPickle": ["copy_reg", "types", "string"],
            "cStringIO": ["copy_reg"],
            "parser": ["copy_reg"],
            "codecs": ["encodings"],
            "_sre": ["copy_reg"],
            }
        from tools.modulefinder import ModuleFinder

        for script in self.distribution.scripts:

            excludes = ["os2", "posix", "dos", "mac", "macfs", "macfsn",
                        "MACFS", "pwd"] + self.excludes

            # Use the modulefinder to find dependend modules.
            #
            self.announce("Searching modules needed to run '%s' on path:" % \
                          script)
            self.announce(repr(extra_path + sys.path))

            script_base = os.path.splitext(os.path.basename(script))[0]
            final_dir = os.path.join(self.dist_dir, script_base)

            if self.debug:
                exe_name = os.path.join(final_dir, script_base+'_d.exe')
            else:
                exe_name = os.path.join(final_dir, script_base+'.exe')

            ext = os.path.splitext(script)[1]
            use_runw = ((string.lower(ext) == '.pyw') or self.windows) \
                       and not self.console

            mf = ModuleFinder (path=extra_path + sys.path,
                              debug=0,
                              excludes=excludes)

            for f in self.support_modules():
                mf.load_file(f)

            for f in self.includes:
                try:
                    file, pathname, desc = imp.find_module(f, extra_path + sys.path)
                except ImportError:
                    # Strange! Modules found via registry entries are only
                    # found by imp.find_module if NO path specified.
                    try:
                        file, pathname, desc = imp.find_module(f)
                    except ImportError:
                        continue
                mf.load_module(f, file, pathname, desc)

            mf.run_script(script)

            force_imports = []
            # first pass over modulefinder results, insert modules from import_hack
            for item in mf.modules.values():
                if item.__name__ in import_hack.keys():
                    mods = import_hack[item.__name__]
                    force_imports.extend(mods)
                    for f in mods:
                        file, pathname, desc = imp.find_module(f, extra_path + sys.path)
                        mf.load_module(f, file, pathname, desc)

            # Retrieve modules from modulefinder
            py_files = []
            extensions = []
            for item in mf.modules.values():
                src = item.__file__
                if src and src != script:
                    if src[-3:] == ".py":
                        py_files.append(item)
                        continue
                    for suffix in _c_suffixes:
                        if endswith(src, suffix):
                            extensions.append(item)
                            break
                    else:
                        raise RuntimeError \
                              ("Don't know how to handle '%s'" % src)

            # byte compile the python modules into the target directory
            byte_compile(py_files,
                         target_dir=collect_dir,
                         optimize=self.optimize, force=self.force,
                         verbose=self.verbose,
                         dry_run=self.dry_run)

            missing = filter(lambda n, e=excludes: n not in e, \
                             mf.badmodules.keys())
            
            # if build debug binary, use debug extension modules
            # instead of the release versions.
            missing, extensions = self.fix_extmodules(missing, extensions,
                                                      sys.path + extra_path)

            if missing:
                self.warn("*" * 48)
                self.warn("* The following modules were not found:")
                for name in missing:
                    mod = mf.badmodules.get(name, None)
                    self.warn("*   %15s: %s" % (name, mod))
                self.warn("*" * 48)

            self.mkpath(final_dir)

            # Collect all the dlls, so that binary dependencies can be
            # resolved.

            # Note: Some extension modules (from win32all: pythoncom and pywintypes)
            # are located via registry entries. Our ext_mapping dictionary
            # maps the module name to the filename. At runtime,
            # the import hook does not have to search the filesystem for modules,
            # but can lookup the needed file directly.
            # Also, this way the registry entries are contained in the
            # dict.
            # This distionary will later be written to the source file
            # used to install the import hook.
            #
            # XXX Problem remaining:
            # If win32api is somehow included, PyWinTypesxx.dll is found
            # in the binary dependencies.
            #
            # But because it is not imported, it is not found by modulefinder,
            # and so the registry mapping is not found....
            #
            # We cold solve this by reading the registry directly.
            # Python 1.5 cannot do this, so we cannot use _winreg,
            # and so we have
            
            ext_mapping = {}
            dlls = []
            for ext_module in extensions:
                pathname = ext_module.__file__
                suffix = self.find_suffix(pathname)
                ext_mapping[ext_module.__name__] = (os.path.basename(pathname), suffix)
                dlls.append(pathname)

            # copy support files and the script itself
            #
            thisfile = sys.modules['py2exe.py2exe'].__file__
            src = os.path.join(os.path.dirname(thisfile),
                                   "support.py")

            self.mkpath(os.path.join(collect_dir, "Scripts"))
            # Scripts\\support.py must be forced to be rewritten!
            dst = os.path.join(collect_dir, "Scripts\\support.py")
            file_util.copy_file(src, dst, update=0,
                                verbose=self.verbose,
                                dry_run=self.dry_run)

            if not self.dry_run:
                file = open(dst, "a")
                file.write("_extensions_mapping = %s\n" % `ext_mapping`)
                if force_imports:
                    file.write("import %s\n" % string.join(force_imports, ', '))
                file.close()

            self.announce("force_imports = %s" % string.join(force_imports, ', '))
            self.announce("ext_mapping = {")
            for key, value in ext_mapping.items():
                self.announce(" %s: %s" % (`key`, `value`))
            self.announce("}")

            self.copy_file(script,
                           os.path.join(collect_dir,
                                        "Scripts\\__main__.py"))
                           
            # The archive must not be in collect-dir, otherwise
            # it may include a (partial) copy of itself
            archive_basename = os.path.join(self.bdist_dir, script_base)

            arcname = self.make_archive(archive_basename, "zip",
                                        root_dir=collect_dir)

            script_path = os.path.join("Scripts", os.path.basename(script))

            self.create_exe(exe_name, arcname, use_runw)

            self.copy_additional_files(final_dir)

            self.copy_dependend_dlls(final_dir, use_runw, dlls)

        if not self.keep_temp:
            remove_tree(self.bdist_dir, self.verbose, self.dry_run)

    # run()

    def find_suffix(self, filename):
        # given a filename (usually of type C_EXTENSION),
        # find the corresponding entry from imp.get_suffixes
        # based on the extension
        extension = os.path.splitext(filename)[1]
        for desc in imp.get_suffixes():
            if desc[0] == extension:
                return desc
        # XXX Should not occur!
        raise "Error"

    def copy_dependend_dlls(self, final_dir, use_runw, dlls):
        import py2exe_util
        sysdir = py2exe_util.get_sysdir()
        windir = py2exe_util.get_windir()
        # This is the tail of the path windows uses when looking for dlls
        # XXX On Windows NT, the SYSTEM directory is also searched
        # (sysdir is SYSTEM32)
        exedir = os.path.dirname(sys.executable)
        syspath = os.environ['PATH']
        loadpath = string.join([exedir, sysdir, windir, syspath], ';')

        images = [self.get_exe_stub(use_runw)] + dlls

        self.announce("Resolving binary dependencies")
        
        alldlls = bin_depends(loadpath, images)
        alldlls.remove(self.get_exe_stub(use_runw))

        for src in alldlls:
            basename = os.path.basename(src)
            if string.lower(basename) in self.EXCLUDE:
                continue
            dst = os.path.join(final_dir, basename)
            try:
                self.copy_file(src, dst)
            except Exception, detail:
                import traceback
                traceback.print_exc()

         
    # DLLs to be excluded
    # XXX This list is NOT complete (it cannot be)
    # Note: ALL ENTRIES MUST BE IN LOWER CASE!
    EXCLUDE = (
        "advapi32.dll",
        "comctl32.dll",
        "gdi32.dll",
        "kernel32.dll",
        "msvcirt.dll",  # ???
        "msvcrt.dll",   # normally redistributable
        "msvcrtd.dll",  # not redistributable
        "ntdll.dll",
        "ole32.dll",
        "oleaut32.dll",
        "rpcrt4.dll",
        "shell32.dll",
        "shlwapi.dll",
        "user32.dll",
        "winmm.dll",
        "winspool.drv",
        "ws2_32.dll",
        "ws2help.dll",
        "wsock32.dll",
        )

    def fix_extmodules(self, missing, extensions, path):
        if not self.debug:
            return missing, extensions
        # if building a debug binary, replace <module>.pyd or <module>.dll
        # with <module>_d.pyd or <module>_d.pyd (but they have to be
        # found again by imp.find_module)
        fixed_modules = []
        for ext_module in extensions:
            name = ext_module.__name__
            try:
                file = imp.find_module(name + '_d', path)[1]
            except ImportError:
                missing.append(name)
            else:
                fixed_modules.append(Module(name=name, file=file))

        # extension modules may be in missing because they may be present
        # in debug but not in release mode: search again
        for name in missing[:]:
            try:
                _, file, desc = imp.find_module(name + '_d', path)
            except ImportError:
                pass
            else:
                if desc[2] == imp.C_EXTENSION:
                    missing.remove(name)
                    fixed_modules.append(Module(name=name, file=file))
        return missing, fixed_modules

    def copy_additional_files(self, final_dir):
        # Some python versions (1.5) import the 'exceptions'
        # module BEFORE we can install our importer.
        file, pathname, desc = imp.find_module("exceptions")
        if file:
            # This module is not builtin
            file.close()
            module = Module(name="exceptions", file=pathname)
            byte_compile([module],
                         target_dir=final_dir,
                         optimize=self.optimize, force=self.force,
                         verbose=self.verbose,
                         dry_run=self.dry_run)

    def support_modules(self):
        import imp
        try:
            return [imp.find_module("imputil")[1]]
        except ImportError:
            import tools
            return [imp.find_module("imputil", tools.__path__)[1]]

    def create_exe (self, exe_name, arcname, use_runw):
        import struct

        self.announce("creating %s" % exe_name)

        header = struct.pack("<iii",
                             self.optimize, # optimize
                             0, # verbose
                             0x0bad3bad,
                             )
        file = open(exe_name, "wb")
        file.write(self.get_exe_bytes(use_runw))
        file.write(header)
        file.write(open(arcname, "rb").read())
        file.close()

    # create_exe()

    def get_exe_stub(self, use_runw):
        thismod = sys.modules['distutils.command.py2exe']
        directory = os.path.dirname(thismod.__file__)
        if use_runw:
            basename = "run_w"
        else:
            basename = "run"
        if self.debug:
            basename = basename + '_d'
        return os.path.join(directory, basename+'.exe')

    def get_exe_bytes(self, use_runw):
        fname = self.get_exe_stub(use_runw)
        self.announce("Using stub '%s'" % fname)
        return open(fname, "rb").read()

    # get_exe_bytes()

# class py2exe

def bin_depends(path, images):
    import py2exe_util
    images = list(images[:])
    dependents = []
    while images:
        for image in images:
            images.remove(image)
            image = os.path.abspath(image)
            if image not in dependents:
                dependents.append(image)
                loadpath = os.path.dirname(image) + ';' + path
                for dll in py2exe_util.depends(image, loadpath):
                    if dll not in images:
                        images.append(dll)
    return dependents
    


def endswith(str, substr):
    return str[-len(substr):] == substr

class Module:
    def __init__(self, name, file, path=None):
        self.__name__ = name
        self.__file__ = file
        self.__path__ = path
    def __repr__(self):
        if self.__path__:
            return "Module(%s, %s)" %\
                   (`self.__name__`, `self.__file__`, `self.__path__`)
        else:
            return "Module(%s, %s)" % (`self.__name__`, `self.__file__`)

def byte_compile(py_files, optimize=0, force=0,
                 target_dir=None, verbose=1, dry_run=0,
                 direct=None):

    if direct is None:
        direct = (__debug__ and optimize == 0)

    # "Indirect" byte-compilation: write a temporary script and then
    # run it with the appropriate flags.
    if not direct:
        from tempfile import mktemp
        from distutils.util import execute
        script_name = mktemp(".py")
        if verbose:
            print "writing byte-compilation script '%s'" % script_name
        if not dry_run:
            script = open(script_name, "w")
            script.write("""\
from py2exe.py2exe import byte_compile, Module
files = [
""")

            for f in py_files:
                script.write("Module(%s, %s, %s),\n" % \
                (`f.__name__`, `f.__file__`, `f.__path__`))
            script.write("]\n")
            script.write("""
byte_compile(files, optimize=%s, force=%s,
             target_dir=%s,
             verbose=%s, dry_run=0,
             direct=1)
""" % (`optimize`, `force`, `target_dir`, `verbose`))

            script.close()

        cmd = [sys.executable, script_name]
        if optimize == 1:
            cmd.insert(1, "-O")
        elif optimize == 2:
            cmd.insert(1, "-OO")
        spawn(cmd, verbose=verbose, dry_run=dry_run)
        execute(os.remove, (script_name,), "removing %s" % script_name,
                verbose=verbose, dry_run=dry_run)


    else:
        from py_compile import compile
        from distutils.dir_util import mkpath

        for file in py_files:
            if file.__file__[-3:] != ".py":
                raise RuntimeError, "cannot compile '%s'" % file.__file__

            # Terminology from the py_compile module:
            #   cfile - byte-compiled file
            #   dfile - purported source filename (same as 'file' by default)
            cfile = string.replace(file.__name__, '.', '\\')

            if file.__path__:
                dfile = cfile + '\\__init__.py' + (__debug__ and 'c' or 'o')
            else:
                dfile = cfile + '.py' + (__debug__ and 'c' or 'o')
            if target_dir:
                cfile = os.path.join(target_dir, dfile)

            if force or newer(file.__file__, cfile):
                if verbose:
                    print "byte-compiling %s to %s" % (file.__file__, dfile)
                if not dry_run:
                    mkpath(os.path.dirname(cfile))
                    compile(file.__file__, cfile, dfile)
            else:
                if verbose:
                    print "skipping byte-compilation of %s to %s" % \
                          (file.__file__, dfile)

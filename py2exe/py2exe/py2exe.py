"""distutils.command.py2exe

Implements the Distutils 'py2exe' command: create executable
windows programs from scripts."""

# ToDo:
#
# By creating our own build_interpreter command,
# instead of (ab)using build_ext, we have got some
# problems:
# Should override build_dir so that the python version
# is included in the directory name.

# created 2000/11/14, Thomas Heller

__revision__ = "$Id$"

import sys, os, string
from distutils.core import Command
from distutils.util import get_platform
from distutils.dir_util import create_tree, remove_tree
from distutils.file_util import copy_file
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
# We could be running
#    4. the release binary of the python interpreter pythonxx.dll,
#       extension modules have the filenames <module>.pyd or <module>.dll
#    5. the debug binary of the python interpreter pythonxx.dll,
#       extension modules have the filenames <module>.pyd or <module>.dll
#
# in case 1, __debug__ is true, in cases 2 and 3 __debug__ is false.
# in case 4, imp.get_suffixes() returns something like [('.pyd',...), ('.dll',...), ...]
# in case 5, imp_get_suffixes() returns something like [('_d.pyd',...), ('_d.dll',...), ...]

class py2exe (Command):

    description = "create executable windows programs from scripts"

    # XXX need more options: unbuffered, includes, excludes, ???
    user_options = [
##        ('bdist-dir=', 'd',
##         "temporary directory for creating the distribution"),
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

    # finalize_options()


    def run (self):
        if not self.distribution.scripts:
            # nothing to do
            # should raise an error!
            raise "Error", "Nothing to do"
            return

        self.run_command('build')

        install = self.reinitialize_command('install')
        install.root = os.path.join(self.bdist_dir, "lib")
        install.optimize = install.compile = 0
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
        #   cStrringIO imports string
        #   parser imports copy_reg
        #   codecs imports encodings
        from tools.modulefinder import ModuleFinder

        for script in self.distribution.scripts:

            excludes = ["os2", "posix", "dos", "mac"]

            # Use the modulefinder to find dependend modules.
            #
            self.announce("Searching modules needed to run '%s'" % script)
            m = ModuleFinder (path=extra_path + sys.path,
                              debug=0,
                              excludes=excludes)
            for f in self.support_modules():
                m.load_file(f)
            m.run_script(script)

            missing = filter(lambda m, e=excludes: m not in e, m.badmodules.keys())

            if missing:
                self.warn("*" * 48)
                self.warn("* The following modules were not found:")
                for n in missing:
                    self.warn("*    " + n)
                self.warn("*" * 48)

            # Retrieve modules from modulefinder
            py_files = []
            extensions = []
            for item in m.modules.values():
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
            #
            byte_compile(py_files,
                         target_dir=collect_dir,
                         optimize=self.optimize, force=self.force,
                         verbose=self.verbose,
                         dry_run=self.dry_run)

            script_base = os.path.splitext(os.path.basename(script))[0]
            final_dir = os.path.join(self.dist_dir, script_base)
            self.mkpath(final_dir)

            # copy extension modules, massaging filenames so that they
            # contain the package-name they belong to (if any).
            # They are copied  directly to dist_dir.
            print "COPYING EXTENSIONS TO", final_dir
            for ext_module in extensions:
                src, dst = self.find_extmodule_paths(ext_module)
                self.copy_file(src,
                          os.path.join(final_dir, dst))

            # XXX Should copy pythonxx.dll!

            # copy support files and the script itself
            #
            thisfile = sys.modules['py2exe.py2exe'].__file__
            support = os.path.join(os.path.dirname(thisfile),
                                   "support.py")
            self.mkpath(os.path.join(collect_dir, "Scripts"))
            self.copy_file(support, os.path.join(collect_dir,
                                                 "Scripts\\support.py"))

            self.copy_file(script,
                           os.path.join(collect_dir,
                                        "Scripts\\%s.py" % script_base))
                           
            archive_basename = os.path.join(collect_dir, script_base)

            arcname = self.make_archive(archive_basename, "zip",
                                        root_dir=collect_dir)

            script_path = os.path.join("Scripts", os.path.basename(script))

            if self.debug:
                exe_name = os.path.join(final_dir, script_base+'_d.exe')
            else:
                exe_name = os.path.join(final_dir, script_base+'.exe')

            self.create_exe(exe_name, arcname, script_path)

            self.copy_additional_files(final_dir)

        if not self.keep_temp:
            remove_tree(self.bdist_dir, self.verbose, self.dry_run)

    # run()

    def find_extmodule_paths(self, ext_module):
        # XXX comment missing
        if self.debug:
            src = imp.find_module(ext_module.__name__ + '_d')[1]
            dst = ext_module.__name__ + '_d' # module name
        else:
            src = ext_module.__file__ # pathname
            dst = ext_module.__name__ # module name

        ext = os.path.splitext(src)[1]

        return src, dst + ext

    def copy_additional_files(self, final_dir):
        # Some python versions (1.5) import the 'exceptions'
        # module BEFORE we can install our importer.
        file, pathname, desc = imp.find_module("exceptions")
        if file:
            file.close()
            module = Module(name=name, path=pathname)
            byte_compile([module],
                         target_dir=final_dir,
                         optimize=self.optimize, force=self.force,
                         verbose=self.verbose,
                         dry_run=self.dry_run)

        
        version = (sys.hexversion >> 24), (sys.hexversion >> 16) & 0xff
        if self.debug:
            template = "python%s%s_d.dll"
        else:
            template = "python%s%s.dll"
        pythondll = (template % version)
        for path in string.split(os.environ["PATH"], ';') + sys.path:
            fullpath = os.path.join(path, pythondll)
            if os.path.isfile(fullpath):
                self.copy_file(fullpath,
                          os.path.join(final_dir, pythondll))
                break
        else:
            raise "NOTFOUND", (pythondll, os.environ["PATH"])

    def support_modules(self):
        import imp
        return [imp.find_module("imputil")[1]]

    def create_exe (self, exe_name, arcname, script_name):
        import struct

        base_name = os.path.splitext(os.path.basename(arcname))[0]
        if self.debug:
            base_name = base_name + '_d'

        self.announce("creating %s" % exe_name)

        # Make sure script_name uses backward slashes!
        script_name = string.replace(script_name, '/', '\\')

        # Create a header which contains the name of the script to run
        l = len(script_name)+1
        header = struct.pack("<%dsiiii" % l,
                             script_name,
                             l,
                             self.optimize, # optimize
                             0, # unbuffered
                             0x0bad2bad,
                             )
        ext = os.path.splitext(script_name)[1]
        use_runw = ((string.lower(ext) == '.pyw') or self.windows) \
                   and not self.console

        if use_runw:
            self.announce("Creating a GUI application")
        else:
            self.announce("Creating a CONSOLE application")

        file = open(exe_name, "wb")
        file.write(self.get_exe_bytes(use_runw))
        file.write(header)
        file.write(open(arcname, "rb").read())
        file.close()

    # create_exe()

    def get_exe_bytes(self, use_runw):
        thismod = sys.modules['distutils.command.py2exe']
        directory = os.path.dirname(thismod.__file__)
        if use_runw:
            basename = "run_w"
        else:
            basename = "run"
        if self.debug:
            basename = basename + '_d'
        fname = os.path.join(directory, basename+'.exe')
        self.announce("Using stub '%s'" % fname)
        return open(fname, "rb").read()

    # get_exe_bytes()

# class py2exe

def endswith(str, substr):
    return str[-len(substr):] == substr

def strip_syspath(file, extra_path):
    for p in extra_path + sys.path:
        # XXX Must compare case insensitive on Windows!!!
        if p and string.upper(file[:len(p)]) == string.upper(p):
            return file[len(p)+1:]
    if os.path.isfile(file):
        return file
    raise RuntimeError, ("%s not found on path??" % file, extra_path + sys.path)

# strip_syspath()

class Module:
    def __init__(self, name, file, path=None):
        self.__name__ = name
        self.__file__ = file
        self.__path__ = path

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

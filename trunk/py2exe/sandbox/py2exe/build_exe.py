from distutils.core import Command
from distutils.errors import *
import sys, os, imp

_c_suffixes = [triple[0] for triple in imp.get_suffixes()
               if triple[2] == imp.C_EXTENSION]

def imp_find_module(name):
    # same as imp.find_module, but handles dotted names
    names = name.split('.')
    path = None
    for name in names:
        result = imp.find_module(name, path)
        path = [result[1]]
    return result

def fancy_split(str, sep=","):
    # a split which also strips whitespace from the items
    if not str:
        return []
    return [item.strip() for item in str.split(sep)]

LOADER = """
def __load():
    import imp, os, sys
    dirname = os.path.dirname(sys.executable)
    mod = imp.load_dynamic(__name__, os.path.join(dirname, '%s'))
##    mod.frozen = 1
__load()
del __load
"""

class py2exe(Command):
    description = ""
    # List of option tuples: long name, short name (None if no short
    # name), and help string.
    user_options = [
        ('optimize=', 'O',
         "optimization level: -O1 for \"python -O\", "
         "-O2 for \"python -OO\", and -O0 to disable [default: -O0]"),

        ("excludes=", 'e',
         "comma-separated list of modules to exclude"),
        ("includes=", 'i',
         "comma-separated list of modules to include"),
        ("packages=", 'p',
         "comma-separated list of packages to include"),
        ]

    boolean_options = []

    def initialize_options (self):
        self.optimize = None
        self.includes = None
        self.excludes = None
        self.packages = None
        self.dist_dir = None

    def finalize_options (self):
        if self.optimize is None:
            self.optimize = 0
        self.excludes = fancy_split(self.excludes)
        self.includes = fancy_split(self.includes)
        # includes is stronger than excludes
        for m in self.includes:
            if m in self.excludes:
                self.excludes.remove(m)
        self.packages = fancy_split(self.packages)
        self.set_undefined_options('bdist',
                                   ('dist_dir', 'dist_dir'))

    def run(self):
        bdist_base = self.get_finalized_command('bdist').bdist_base
        self.bdist_dir = os.path.join(bdist_base, 'winexe')

        self.collect_dir = os.path.join(self.bdist_dir, "collect")
        self.mkpath(self.collect_dir)
        self.temp_dir = os.path.join(self.bdist_dir, "temp")
        self.mkpath(self.temp_dir)
        self.mkpath(self.dist_dir)

        self.plat_prepare()

        if 1:
            # XXX separate method?
            dist = self.distribution

            # all of these contain module names
            required_modules = dist.com_dll
            required_modules += dist.com_exe
            required_modules += dist.dll
            required_modules += dist.service

            # and these contains file names
            required_files = dist.windows
            required_files += dist.console

        self.includes.append("zlib") # needed for zipimport
        self.includes.append("warnings") # needed by Python itself

        mf = self.find_needed_modules(required_files, required_modules)

        py_files, extensions = self.parse_mf_results(mf)

        # byte compile the python modules into the target directory
        byte_compile(py_files,
                     target_dir=self.collect_dir,
                     optimize=self.optimize,
                     force=0,
                     verbose=self.verbose,
                     dry_run=self.dry_run)

        # copy the extensions in place
        for item in extensions:
            src = item.__file__
            dst = os.path.join(self.dist_dir, os.path.basename(item.__file__))
            self.copy_file(src, dst)

        # The archive must not be in collect-dir, otherwise
        # it may include a (partial) copy of itself
        archive_basename = os.path.join(self.dist_dir, "library")
        arcname = self.make_archive(archive_basename, "zip",
                                    root_dir=self.collect_dir)


        import pprint
        print
        pprint.pprint(py_files)
        print
        print extensions
        print

        from py2exe_util import add_resource
        for path in self.distribution.console:
            exe_base = os.path.splitext(os.path.basename(path))[0]
            exe_path = os.path.join(self.dist_dir, exe_base + '.exe')

            src = os.path.join(os.path.dirname(__file__), "run.exe")
            self.copy_file(src, exe_path)
            
            script_bytes = open(path, "r").read() + '\000\000'
            add_resource(exe_path, script_bytes, "PYTHONSCRIPT", 1, 0)
            print "resource added, %d bytes" % len(script_bytes)
            
            print "exefile", exe_path
            
        
##        print mf.modules
##        print mf.any_missing()

    def parse_mf_results(self, mf):
        # XXX invisible imports (warnings, encodings(?)
##        {"cPickle": ["copy_reg", "types", "string"],
##         "cStringIO": ["copy_reg"],
##         "parser": ["copy_reg"],
##         "codecs": ["encodings"],
##         "_sre": ["copy_reg"],
         
##         "win32api": ["pywintypes"],
##         "win32ui": ["cStringIO", "traceback"],
##         "pythoncom": ["win32com.server.policy", "win32com.server.util", "pywintypes"],
##         }

        # XXX Tkinter magic. Move into self.run() ?
        tcl_src_dir = tcl_dst_dir = None
        if "Tkinter" in mf.modules.keys():
            pass # XXX

        # Retrieve modules from modulefinder
        py_files = []
        extensions = []
        
        for item in mf.modules.values():
            # Don't include __main__
            if item.__name__ == "__main__":
                continue
            src = item.__file__
            if src:
                if src.endswith(".py"):
                    py_files.append(item)
                    continue
                for suffix in _c_suffixes:
                    if src.endswith(suffix):
                        extensions.append(item)
                        loader = self.create_loader(item)
                        if loader:
                            py_files.append(loader)
                        break
                else:
                    raise RuntimeError \
                          ("Don't know how to handle '%s'" % repr(src))

        self.plat_finalize(mf.modules, py_files, extensions)

        return py_files, extensions

    def plat_finalize(self, modules, py_files, extensions):
        # platform specific code for final adjustments to the
        # file lists
        if sys.platform == "win32":
            from modulefinder import Module
            if "pythoncom" in modules.keys():
                import pythoncom
                extensions.append(Module("pythoncom", pythoncom.__file__))
            if "pywintypes" in modules.keys():
                import pywintypes
                extensions.append(Module("pywintypes", pywintypes.__file__))
        else:
            raise DistutilsError, "Platform %s not yet implemented" % sys.platform

    def create_loader(self, item):
        # Extension modules can not be loaded from zipfiles.
        # So we create a small Python stub to be included in the zipfile,
        # which will then load the extension from the file system.
        #
        # For zlib there must be NO stub, otherwise zipimport wouldn't
        # work correctly!
        if item.__name__ == "zlib":
            return

        # Hm, how to avoid needless recreation of this file?
        pathname = os.path.join(self.temp_dir, "%s.py" % item.__name__)
        # and what about dry_run?
        if self.verbose:
            print "creating loader stub for extension '%s'" % item.__name__
        open(pathname, "w").write(LOADER % os.path.basename(item.__file__))
        from modulefinder import Module
        return Module(item.__name__, pathname)

    def plat_prepare(self):
        # update the self.excludes list to exclude platform specific
        # modules
        if sys.platform == "win32":
            self.excludes += ["os2", "posix", "dos", "mac", "macfs", "macfsn",
                              "macpath",
                              "MACFS", "pwd", "MacOS", "macostools",
                              "EasyDialogs", "termios", "TERMIOS",
                              "java.lang", "org.python.core", "riscos",
                              "riscosenviron", "riscospath", "ce",
                              "os.path"
                              ]
        else:
            raise DistutilsError, "Platform %s not yet implemented" % sys.platform

    def find_needed_modules(self, files, modules):
        # feed Modulefinder with everything, and return it.
        from modulefinder import ModuleFinder
        mf = ModuleFinder(excludes=self.excludes)

        for mod in modules:
            mf.import_hook(mod)

        for path in files:
            mf.run_script(path)

        for mod in self.includes:
            if mod[-2:] == '.*':
                mf.import_hook(mod[:-2], None, ['*'])
            else:
                mf.import_hook(mod)

        for f in self.packages:
            def visit(arg, dirname, names):
                if '__init__.py' in names:
                    arg.append(dirname)
            # Very weird...
            # Find path of package
            try:
                path = imp_find_module(f)[1]
            except ImportError:
                self.warn("No package named %s" % f)
                continue

            packages = []
            # walk the path to find subdirs containing __init__.py files
            os.path.walk(path, visit, packages)

            # scan the results (directory of __init__.py files)
            # first trim the path (of the head package),
            # then convert directory name in package name,
            # finally push into modulefinder.
            for p in packages:
                if p.startswith(path):
                    package = f + '.' + p[len(path)+1:].replace('\\', '.')
                    mf.import_hook(package, None, ["*"])

        return mf

################################################################

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
from py2exe.build_exe import byte_compile, Module
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
        from distutils.dep_util import newer

        for file in py_files:
            if file.__file__[-3:] != ".py":
                raise RuntimeError, "cannot compile '%s'" % file.__file__

            # Terminology from the py_compile module:
            #   cfile - byte-compiled file
            #   dfile - purported source filename (same as 'file' by default)
            cfile = file.__name__.replace('.', '\\')

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
# byte_compile()

# utilities stolen from distutils.dir_util and extended

def _chmod(file):
    os.chmod(file, 0777)

# Helper for force_remove_tree()
def _build_cmdtuple(path, cmdtuples):
    for f in os.listdir(path):
        real_f = os.path.join(path,f)
        if os.path.isdir(real_f) and not os.path.islink(real_f):
            _build_cmdtuple(real_f, cmdtuples)
        else:
            cmdtuples.append((_chmod, real_f))
            cmdtuples.append((os.remove, real_f))
    cmdtuples.append((os.rmdir, path))

def force_remove_tree (directory, verbose=0, dry_run=0):
    """Recursively remove an entire directory tree.  Any errors are ignored
    (apart from being reported to stdout if 'verbose' is true).
    """
    import distutils
    from distutils.util import grok_environment_error
    _path_created = distutils.dir_util._path_created

    if verbose:
        print "removing '%s' (and everything under it)" % directory
    if dry_run:
        return
    cmdtuples = []
    _build_cmdtuple(directory, cmdtuples)
    for cmd in cmdtuples:
        try:
            cmd[0](cmd[1])
            # remove dir from cache if it's already there
            abspath = os.path.abspath(cmd[1])
            if _path_created.has_key(abspath):
                del _path_created[abspath]
        except (IOError, OSError), exc:
            if verbose:
                print grok_environment_error(
                    exc, "error removing %s: " % directory)

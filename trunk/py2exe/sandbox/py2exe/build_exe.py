################################################################
# Todo:
#
# Rename the zipfile keyword arg to the setup function to something
# more sensible (?)
#
# How to include win32com.server.policy, and exclude win32com.server.dispatcher
# for com servers ?

################################################################
# Non-Bugs - What works?
#
# Can build simple console programs
# A trivial wxPython program
# gui programs without console

################################################################
# Bugs:
#
# win32com.client.Dispatch programs fail with:

##Traceback (most recent call last):
##  File "<string>", line 16, in ?
##  File "win32com\client\__init__.pyc", line 12, in ?
##  File "win32com\client\gencache.pyc", line 528, in ?
##  File "win32com\client\gencache.pyc", line 44, in __init__
##  File "win32com\client\gencache.pyc", line 515, in Rebuild
##  File "win32com\client\gencache.pyc", line 49, in _SaveDicts
##  File "win32com\client\gencache.pyc", line 96, in GetGeneratePath
##IOError: [Errno 2] No such file or directory:
#      '...\\test\\dist\\application.zip\\win32com\\gen_py\\__init__.py'

from distutils.core import Command
from distutils.spawn import spawn
from distutils.errors import *
import sys, os, imp

_c_suffixes = [triple[0] for triple in imp.get_suffixes()
               if triple[2] == imp.C_EXTENSION]

# consider adding this to our "extended options"??
EXCLUDED_DLLS = ["dapi.dll", "MAPI32.dll"] # sigh

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
    path = os.path.join(dirname, '%s')
    mod = imp.load_dynamic(__name__, path)
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
         ('unbuffered', 'u',
         "unbuffered binary stdout and stderr"),

        ("excludes=", 'e',
         "comma-separated list of modules to exclude"),
        ("includes=", 'i',
         "comma-separated list of modules to include"),
        ("packages=", 'p',
         "comma-separated list of packages to include"),
        ]

    boolean_options = ['unbuffered']

    def initialize_options (self):
        # hack in extra options - if the main setup script defines an object
        # py2exe_options, default some extra options from that.
        try:
            extra_options = __import__('__main__').py2exe_options
            # if class/instance etc, get the dics.
            extra_options = getattr(extra_options, "__dict__", extra_options)
        except (ImportError, AttributeError):
            extra_options = []
        
        self.unbuffered = extra_options.get("unbuffered", 0)
        self.optimize = extra_options.get("optimize", 0)
        self.includes = extra_options.get("include")
        self.excludes = extra_options.get("excludes")
        self.packages = extra_options.get("packages")
        self.dist_dir = extra_options.get("dist_dir")
        self.ext_mapping = extra_options.get("ext_mapping", {})
        self.bitmap_resources = extra_options.get("bitmap_resources", [])
        self.icon_resources = extra_options.get("icon_resources", [])

    def finalize_options (self):
        self.optimize = int(self.optimize)
        self.excludes = fancy_split(self.excludes)
        self.includes = fancy_split(self.includes)
        # includes is stronger than excludes
        for m in self.includes:
            if m in self.excludes:
                self.excludes.remove(m)
        self.packages = fancy_split(self.packages)
        self.set_undefined_options('bdist',
                                   ('dist_dir', 'dist_dir'))
        for bmp_id, bmp_filename in self.bitmap_resources + self.icon_resources:
            if type(bmp_id) != type(0):
                raise DistutilsOptionError, "bitmap ID must be an integer"
            if not os.path.isfile(bmp_filename):
                raise DistutilsOptionError, "Bitmap filename '%s' does not exist" % bmp_filename
        

    def run(self):
        # refactor, refactor, refactor!
        abspath=os.path.abspath
        force_console = True # useful for debugging - refactor this too :)
        bdist_base = self.get_finalized_command('bdist').bdist_base
        self.bdist_dir = os.path.join(bdist_base, 'winexe')

        self.collect_dir = abspath(os.path.join(self.bdist_dir, "collect"))
        self.mkpath(self.collect_dir)
        self.temp_dir = abspath(os.path.join(self.bdist_dir, "temp"))
        self.dist_dir = abspath(self.dist_dir)
        self.mkpath(self.temp_dir)
        self.mkpath(self.dist_dir)

        self.plat_prepare()

        if 1:
            # XXX separate method?
            dist = self.distribution

            # all of these contain module names
            required_modules = dist.com_server[:]
            required_modules += dist.service

            # and these contains file names
            required_files = dist.windows[:]
            required_files += dist.console

        self.includes.append("zlib") # needed for zipimport
        self.includes.append("warnings") # needed by Python itself
##        self.packages.append("encodings")

        mf = self.find_needed_modules(required_files, required_modules)

        py_files, extensions = self.parse_mf_results(mf)

        # byte compile the python modules into the target directory
        print "*** byte compile python files ***"
        byte_compile(py_files,
                     target_dir=self.collect_dir,
                     optimize=self.optimize,
                     force=0,
                     verbose=self.verbose,
                     dry_run=self.dry_run)

        print "*** copy extensions ***"
        # copy the extensions to the target directory
        for item in extensions:
            src = item.__file__
            # It would be nice if we could change the extensions
            # filename to include the full package.module name, for
            # example 'wxPython.wxc.pyd'
            # But this won't work, because this would also rename
            # pythoncom23.dll into pythoncom.dll, and win32com contains
            # magic which relies on this exact filename.
##            base, ext = os.path.splitext(os.path.basename(item.__file__))
##            dst = os.path.join(self.dist_dir, item.__name__ + ext)
            dst = os.path.join(self.dist_dir, os.path.basename(item.__file__))
            self.copy_file(src, dst)

        archive_name = os.path.join(self.dist_dir, dist.zipfile)
        arcname = self.make_archive(archive_name, "zip",
                                    root_dir=self.collect_dir)


        # find and copy binary dependencies
        dlls = [item.__file__ for item in extensions]
        
##        extra_path = ["."] # XXX
        extra_path = []
        dlls, unfriendly_dlls = self.find_dependend_dlls(0, dlls,
                                                         extra_path + sys.path)

        for item in extensions:
            if item.__file__ in dlls:
                dlls.remove(item.__file__)

        print "*** copy dlls ***"
        for dll in dlls.items() + unfriendly_dlls.items():
            dst = os.path.join(self.dist_dir, os.path.basename(dll))
            self.copy_file(dll, dst)

        # build the executables
        self.build_executables(dist.console, "run.exe", arcname)
        self.build_executables(dist.windows, "run_w.exe", arcname)
        self.build_services(dist.service, "run_svc.exe", arcname)

        if dist.com_server:
            if force_console: com_exe_template = "run.exe"
            else: com_exe_template = "run_w.exe"
            self.build_comservers(dist.com_server, com_exe_template, arcname)
            self.build_comservers(dist.com_server, "run_dll.dll", arcname)

        if mf.any_missing():
            print "The following modules appear to be missing"
            print mf.any_missing()

    def get_boot_script(self, boot_type):
        # return the filename of the script to use for com servers.
        thisfile = sys.modules['py2exe.build_exe'].__file__
        return os.path.join(os.path.dirname(thisfile),
                            "boot_" + boot_type + ".py")

    def build_comservers(self, module_names, template, arcname):
        # Build a dll and an exe executable hosting all the com
        # objects listed in module_names.
        # The basename of the dll/exe is the last part of the first module.
        # Do we need a way to specify the name of the files to be built?
        fname = module_names[0].split(".")[-1]
        boot = self.get_boot_script("com_servers")
        dst = os.path.join(self.temp_dir, "%s.py" % fname)

        # We take the boot_com_servers.py script, write the required
        # module names into it, and use it as the script to be run.
        ofi = open(dst, "w")
        ofi.write("com_module_names = %s\n" % module_names)
        ofi.write(open(boot, "r").read())
        ofi.close()

        self.build_executables([dst], template, arcname)

    def get_service_names(self, module_name):
        # import the script with every side effect :)
        __import__(module_name)
        mod = sys.modules[module_name]
        for name, klass in mod.__dict__.items():
            if hasattr(klass, "_svc_name_"):
                break
        else:
            raise RuntimeError, "No services in module"
        deps = ()
        if hasattr(klass, "_svc_deps_"):
            deps = klass._svc_deps_
        return klass.__name__, klass._svc_name_, klass._svc_display_name_, deps

    def build_services(self, module_names, template, arcname):
        # services still need a little thought.  It should be possible
        # to host many modules in a single service - but pythonservice.exe
        # isn't really there yet.
        from py2exe_util import add_resource
        assert len(module_names)==1, "We only support one service module"
        module_name = module_names[0]
        fname = module_name.split(".")[-1]
        boot = self.get_boot_script("service")
        dst = os.path.join(self.temp_dir, "%s.py" % fname)

        # We take the boot_service.py script, write the required
        # module names into it, and use it as the script to be run.
        ofi = open(dst, "w")
        ofi.write("service_module_names = ['%s']\n" % module_name)
        ofi.write(open(boot, "r").read())
        ofi.close()

        exe_path = os.path.join(self.dist_dir, fname + ".exe")

        src = os.path.join(os.path.dirname(__file__), template)
        self.copy_file(src, exe_path)

        # the standard resources
        import struct
        si = struct.pack("iii",
                            0x78563412, # a magic value,
                            self.optimize,
                            self.unbuffered,
                            ) + os.path.basename(arcname) + "\000"

        script_bytes = si + open(dst, "r").read() + '\000\000'
        self.announce("add script resource, %d bytes" % len(script_bytes))
        add_resource(exe_path, script_bytes, "PYTHONSCRIPT", 1, 0)
        # and the service specific resources.
        from resources.StringTables import StringTable, RT_STRING
        # resource id in the EXE of the serviceclass,
        # see source/PythonService.cpp
        RESOURCE_SERVICE_NAME = 1016

        st = StringTable()
        klass_name, svc_name, svc_display_name, svc_deps = \
                                            self.get_service_names(module_name)
        st.add_string(RESOURCE_SERVICE_NAME,
                        "%s.%s" % (module_name, klass_name))
        st.add_string(RESOURCE_SERVICE_NAME+1, svc_name)
        st.add_string(RESOURCE_SERVICE_NAME+2, svc_display_name)
        # XXX service probably won't have a | in them?
        st.add_string(RESOURCE_SERVICE_NAME+3, "|".join(svc_deps))
        for id, data in st.binary():
            add_resource(exe_path, data, RT_STRING, id, 0)

    def build_executables(self, scripts, template, arcname):
        # For each file in scripts, build an executable.
        # template is the exe-stub to use, and arcname is the zipfile
        # containing the python modules.
        from py2exe_util import add_resource, add_icon
        ext = os.path.splitext(template)[1]
        for path in scripts:
            exe_base = os.path.splitext(os.path.basename(path))[0]
            exe_path = os.path.join(self.dist_dir, exe_base + ext)

            src = os.path.join(os.path.dirname(__file__), template)
            self.copy_file(src, exe_path)
            
            import struct
            si = struct.pack("iii",
                             0x78563412, # a magic value,
                             self.optimize,
                             self.unbuffered,
                             ) + os.path.basename(arcname) + "\000"
            
            script_bytes = si + "import sys;sys.frozen=1\n" + open(path, "r").read() + '\000\000'
            self.announce("add script resource, %d bytes" % len(script_bytes))
            add_resource(exe_path, script_bytes, "PYTHONSCRIPT", 1, 0)
            RT_BITMAP=2
            for bmp_id, bmp_filename in self.bitmap_resources:
                bmp_data = open(bmp_filename, "rb").read()
                # skip the 14 byte bitmap header.
                add_resource(exe_path, bmp_data[14:], RT_BITMAP, bmp_id, False)
            for ico_id, ico_filename in self.icon_resources:
                add_icon(exe_path, ico_filename, ico_id)
                

    def find_dependend_dlls(self, use_runw, dlls, pypath):
        import py2exe_util
        sysdir = py2exe_util.get_sysdir()
        windir = py2exe_util.get_windir()
        # This is the tail of the path windows uses when looking for dlls
        # XXX On Windows NT, the SYSTEM directory is also searched
        exedir = os.path.dirname(sys.executable)
        syspath = os.environ['PATH']
        loadpath = ';'.join([exedir, sysdir, windir, syspath])

        # Found by Duncan Booth:
        # It may be possible that bin_depends needs extension modules,
        # so the loadpath must be extended by our python path.
        loadpath = loadpath + ';' + ';'.join(pypath)

##XXX        images = [self.get_exe_stub(use_runw)] + dlls
        images = dlls # XXX

        self.announce("Resolving binary dependencies:")
        
        alldlls, warnings = bin_depends(loadpath, images)
        for dll in alldlls:
            self.announce("  %s" % dll)
##XXX        alldlls.remove(self.get_exe_stub(use_runw))

        for dll in alldlls:
            if dll in dlls:
                continue
            fname, ext = os.path.splitext(os.path.basename(dll))
            try:
                result = imp.find_module(fname, pypath)
            except ImportError:
                pass
            else:
                self.ext_mapping[fname] = (os.path.basename(dll), result[2])
                    
        return alldlls, warnings
    # find_dependend_dlls()

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
            # There may be __main__ modules (from mf.run_script), but
            # we don't need it in the zipfile we build.
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
        # Without a need for the extensions directory to be in sys.path!
        #
        # For zlib there must be NO stub, otherwise zipimport wouldn't
        # work correctly!
        if item.__name__ == "zlib":
            return

        # Hm, how to avoid needless recreation of this file?
        pathname = os.path.join(self.temp_dir, "%s.py" % item.__name__)
        # and what about dry_run?
        if self.verbose:
            print "creating loader stub for extension '%s' as '%s'" % \
                  (item.__name__, pathname)

        fname = os.path.basename(item.__file__)
        source = LOADER % fname
        if not self.dry_run:
            open(pathname, "w").write(source)
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
        from modulefinder import ModuleFinder, ReplacePackage

        ReplacePackage("_xmlplus", "xml")
        mf = ModuleFinder(excludes=self.excludes)

        for mod in modules:
            mf.import_hook(mod)

        for path in files:
            mf.run_script(path)

        if self.distribution.com_server:
            mf.run_script(self.get_boot_script("com_servers"))

        if self.distribution.service:
            mf.run_script(self.get_boot_script("service"))

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

class FileSet:
    # A case insensitive but case preserving set of files
    def __init__(self, *args):
        self._dict = {}
        for arg in args:
            self.add(arg)

    def __repr__(self):
        return "<FileSet %s at %x>" % (self._dict.values(), id(self))

    def add(self, fname):
        self._dict[fname.upper()] = fname

    def remove(self, fname):
        del self._dict[fname.upper()]

    def contains(self, fname):
        return fname.upper() in self._dict.keys()

    def __getitem__(self, index):
        key = self._dict.keys()[index]
        return self._dict[key]

    def __len__(self):
        return len(self._dict)

    def items(self):
        return self._dict.values()

# class FileSet()

def bin_depends(path, images):
    import py2exe_util
    warnings = FileSet()
    images = FileSet(*images)
    dependents = FileSet()
    while images:
        for image in images:
            images.remove(image)
            if not dependents.contains(image):
                dependents.add(image)
                abs_image = os.path.abspath(image)
                loadpath = os.path.dirname(abs_image) + ';' + path
                for result in py2exe_util.depends(image, loadpath).items():
                    dll, uses_import_module = result
                    if not images.contains(dll) \
                       and not dependents.contains(dll) \
                       and not isSystemDLL(dll):
                        images.add(dll)
                        if uses_import_module:
                            warnings.add(dll)
    return dependents, warnings
    
def isSystemDLL(pathname):
    if os.path.basename(pathname).lower() in EXCLUDED_DLLS:
        return 1
    # How can we determine whether a dll is a 'SYSTEM DLL'?
    # Is it sufficient to use the Image Load Address?
    import struct
    file = open(pathname, "rb")
    if file.read(2) != "MZ":
        raise Exception, "Seems not to be an exe-file"
    file.seek(0x3C)
    pe_ofs = struct.unpack("i", file.read(4))[0]
    file.seek(pe_ofs)
    if file.read(4) != "PE\000\000":
        raise Exception, ("Seems not to be an exe-file", pathname)
    file.read(20 + 28) # COFF File Header, offset of ImageBase in Optional Header
    imagebase = struct.unpack("I", file.read(4))[0]
    return not (imagebase < 0x70000000)

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
from py2exe.build_exe import byte_compile
from modulefinder import Module
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

# utilities hacked from distutils.dir_util

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

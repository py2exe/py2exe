# Todo:
#
# Make 'unbuffered' a per-target option

from distutils.core import Command
from distutils.spawn import spawn
from distutils.errors import *
import sys, os, imp, types
import marshal
import zipfile

import _sre # any module known to be a .pyd
is_debug_build = _sre.__file__.find("_d")>=0

if is_debug_build:
    python_dll = "python%d%d_d.dll" % sys.version_info[:2]
else:
    python_dll = "python%d%d.dll" % sys.version_info[:2]

# resource constants
RT_BITMAP=2

_c_suffixes = [_triple[0] for _triple in imp.get_suffixes()
               if _triple[2] == imp.C_EXTENSION]

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
    # passing a list or tuple will return it unchanged
    if str is None:
        return []
    if hasattr(str, "split"):
        return [item.strip() for item in str.split(sep)]
    return str

LOADER = """
def __load():
    import imp, os, sys
    dirname = sys.prefix
    path = os.path.join(dirname, '%s')
    #print "py2exe extension module", __name__, "->", path
    mod = imp.load_dynamic(__name__, path)
##    mod.frozen = 1
__load()
del __load
"""

# A very loosely defined "target".  We assume either a "script" or "modules"
# attribute.  Some attributes will be target specific.
class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # If modules is a simple string, assume they meant list
        m = self.__dict__.get("modules")
        if m and type(m) in types.StringTypes:
            self.modules = [m]
    def get_dest_base(self):
        dest_base = getattr(self, "dest_base", None)
        if dest_base: return dest_base
        script = getattr(self, "script", None)
        if script:
            return os.path.basename(os.path.splitext(script)[0])
        modules = getattr(self, "modules", None)
        assert modules, "no script, modules or dest_base specified"
        return modules[0].split(".")[-1]

    def validate(self):
        resources = getattr(self, "bitmap_resources", []) + \
                    getattr(self, "icon_resources", [])
        for r_id, r_filename in resources:
            if type(r_id) != type(0):
                raise DistutilsOptionError, "Resource ID must be an integer"
            if not os.path.isfile(r_filename):
                raise DistutilsOptionError, "Resource filename '%s' does not exist" % r_filename

def FixupTargets(targets, default_attribute):
    if not targets:
        return targets
    ret = []
    for target_def in targets:
        if type(target_def) in types.StringTypes :
            # Create a default target object, with the string as the attribute
            target = Target(**{default_attribute: target_def})
        else:
            if not target_def.has_key(default_attribute):
                raise DistutilsOptionError, \
                      "This target requires a '%s' definition" % default_attribute
            target = Target(**target_def)
        target.validate()
        ret.append(target)
    return ret

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
        ("includes=", 'i',
         "comma-separated list of modules to include"),
        ("packages=", 'p',
         "comma-separated list of packages to include"),
        ]

    boolean_options = ['unbuffered', 'optimize']

    def initialize_options (self):
        self.unbuffered = 0
        self.optimize = 0
        self.includes = None
        self.excludes = None
        self.packages = None
        self.dist_dir = None
        self.dll_excludes = None
        self.typelibs = None

    def finalize_options (self):
        self.excludes = fancy_split(self.excludes)
        self.includes = fancy_split(self.includes)
        # includes is stronger than excludes
        for m in self.includes:
            if m in self.excludes:
                self.excludes.remove(m)
        self.packages = fancy_split(self.packages)
        self.set_undefined_options('bdist',
                                   ('dist_dir', 'dist_dir'))
        self.dll_excludes = fancy_split(self.dll_excludes)

    def run(self):
        self.create_directories()
        self.plat_prepare()
        self.fixup_distribution()

        dist = self.distribution

        # all of these contain module names
        required_modules = []
        for target in dist.com_server + dist.service:
            required_modules.extend(target.modules)
        # and these contains file names
        required_files = [target.script
                          for target in dist.windows + dist.console]

        ################
        # refactor, refactor, refactor!

        # XXX zlib is only needed for zipimport from compressed archives (?)
        self.includes.append("zlib") # needed for zipimport
        self.includes.append("warnings") # needed by Python itself
##        self.packages.append("encodings")

        from modulefinder import ModuleFinder, ReplacePackage
        ReplacePackage("_xmlplus", "xml")
        mf = ModuleFinder(excludes=self.excludes)

        if self.typelibs:
            print "*** generate typelib stubs ***"
            from distutils.dir_util import mkpath
            genpy_temp = os.path.join(self.temp_dir, "win32com", "gen_py")
            mkpath(genpy_temp)
            dict_dat, num_stubs = collect_win32com_genpy(genpy_temp,
                                                         self.typelibs)
            print "collected %d stubs from %d type libraries" \
                  % (num_stubs, len(self.typelibs))
            mf.load_package("win32com.gen_py", genpy_temp)
            self.packages.append("win32com.gen_py")
            genpy_dir = os.path.join(self.collect_dir, "win32com", "gen_py")
            mkpath(genpy_dir)
            self.copy_file(dict_dat, genpy_dir)

        print "*** searching for required modules ***"
        self.find_needed_modules(mf, required_files, required_modules)

        print "*** parsing results ***"
        py_files, extensions = self.parse_mf_results(mf)

        print "*** finding dlls needed ***"
        dlls = self.find_dlls(extensions)
        self.plat_finalize(mf.modules, py_files, extensions, dlls)

        print "*** create binaries ***"
        self.create_binaries(py_files, extensions, dlls)

        if mf.any_missing():
            print "The following modules appear to be missing"
            print mf.any_missing()


    def find_dlls(self, extensions):
        dlls = [item.__file__ for item in extensions]
##        extra_path = ["."] # XXX
        extra_path = []
        dlls, unfriendly_dlls = self.find_dependend_dlls(0, dlls,
                                                         extra_path + sys.path,
                                                         self.dll_excludes)
        # dlls contains the path names of all dlls we need.
        # If a dll uses a function PyImport_ImportModule (or what was it?),
        # it's name is additionally in unfriendly_dlls.
        for item in extensions:
            if item.__file__ in dlls:
                dlls.remove(item.__file__)
        return dlls

    def create_directories(self):
        bdist_base = self.get_finalized_command('bdist').bdist_base
        self.bdist_dir = os.path.join(bdist_base, 'winexe')

        self.collect_dir = os.path.abspath(os.path.join(self.bdist_dir, "collect"))
        self.mkpath(self.collect_dir)

        self.temp_dir = os.path.abspath(os.path.join(self.bdist_dir, "temp"))
        self.mkpath(self.temp_dir)

        self.dist_dir = os.path.abspath(self.dist_dir)
        self.mkpath(self.dist_dir)

        self.lib_dir = os.path.join(self.dist_dir,
                                    os.path.dirname(self.distribution.zipfile))
        self.mkpath(self.lib_dir)

    def create_binaries(self, py_files, extensions, dlls):
        dist = self.distribution
        
        # byte compile the python modules into the target directory
        print "*** byte compile python files ***"
        byte_compile(py_files,
                     target_dir=self.collect_dir,
                     optimize=self.optimize,
                     force=0,
                     verbose=self.verbose,
                     dry_run=self.dry_run)

        all_files = []

        print "*** copy extensions ***"
        # copy the extensions to the target directory
        for item in extensions:
            src = item.__file__
            # XXX It seems the following comment is no longer true...
            # have to check
            #
            # It would be nice if we could change the extensions
            # filename to include the full package.module name, for
            # example 'wxPython.wxc.pyd'
            # But this won't work, because this would also rename
            # pythoncom23.dll into pythoncom.dll, and win32com contains
            # magic which relies on this exact filename.
            # So we do it via a custom loader - see create_loader()
            dst = os.path.join(self.lib_dir, os.path.basename(item.__file__))
            self.copy_file(src, dst)
            all_files.append(dst)

        # create the shared zipfile containing all Python modules
        archive_name = os.path.join(self.lib_dir,
                                    os.path.basename(dist.zipfile))
        arcname = self.make_lib_archive(archive_name, base_dir=self.collect_dir,
                                   verbose=self.verbose, dry_run=self.dry_run)
        all_files.append(arcname)

        print "*** copy dlls ***"
        for dll in dlls:
            base = os.path.basename(dll)
            if base.lower() in self.dlls_in_exedir:
                # These special dlls cannot be in the lib directory,
                # they must go into the exe directory.
                dst = os.path.join(self.exe_dir, base)
            else:
                dst = os.path.join(self.lib_dir, base)
            self.copy_file(dll, dst)
            all_files.append(dst)

        if self.distribution.has_data_files():
            print "*** copy data files ***"
            install_data = self.reinitialize_command('install_data')
            install_data.install_dir = self.dist_dir
            install_data.ensure_finalized()
            install_data.run()

            all_files.extend(install_data.get_outputs())

        # build the executables
        for target in dist.console:
            dst = self.build_executable(target, "run.exe", arcname, target.script)
            all_files.append(dst)
        for target in dist.windows:
            dst = self.build_executable(target, "run_w.exe", arcname, target.script)
            all_files.append(dst)
        for target in dist.service:
            # Note: we may want to give the user the option of using run_w.exe
            dst = self.build_service(target, "run.exe", arcname)
            all_files.append(dst)

        for target in dist.com_server:
            if getattr(target, "create_exe", True):
                # XXX Mark: Hm, should there be an option to build a
                # console version for debugging, or is the regular
                # debug support in win32com sufficient?
                dst = self.build_comserver(target, "run_w.exe", arcname)
                all_files.append(dst)
            if getattr(target, "create_dll", True):
                dst = self.build_comserver(target, "run_dll.dll", arcname)
                all_files.append(dst)

        # XXX debug code!
##        for name in all_files:
##            assert name.startswith(self.dist_dir)
##            print "*", name[len(self.dist_dir)+1:]

    def fixup_distribution(self):
        dist = self.distribution
        
        # Convert our args into target objects.
        dist.com_server = FixupTargets(dist.com_server, "modules")
        dist.service = FixupTargets(dist.service, "modules")
        dist.windows = FixupTargets(dist.windows, "script")
        dist.console = FixupTargets(dist.console, "script")

        # make sure all targets use the same directory, this is
        # also the directory where the pythonXX.dll must reside
        import sets
        paths = sets.Set()
        for target in dist.com_server + dist.service \
                + dist.windows + dist.console:
            paths.add(os.path.dirname(target.get_dest_base()))

        if len(paths) > 1:
            raise DistutilsOptionError, \
                  "all targets must use the same directory: %s" % \
                  [p for p in paths]
        if paths:
            exe_dir = paths.pop() # the only element
            if os.path.isabs(exe_dir):
                raise DistutilsOptionError, \
                      "exe directory must be relative: %s" % exe_dir
            self.exe_dir = os.path.join(self.dist_dir, exe_dir)
            self.mkpath(self.exe_dir)
        else:
            # Do we allow to specify no targets?
            # We can at least build a zipfile...
            self.exe_dir = self.lib_dir

    def get_boot_script(self, boot_type):
        # return the filename of the script to use for com servers.
        thisfile = sys.modules['py2exe.build_exe'].__file__
        return os.path.join(os.path.dirname(thisfile),
                            "boot_" + boot_type + ".py")

    def build_comserver(self, target, template, arcname):
        # Build a dll and an exe executable hosting all the com
        # objects listed in module_names.
        # The basename of the dll/exe is the last part of the first module.
        # Do we need a way to specify the name of the files to be built?

        # Setup the variables our boot script needs.
        vars = {"com_module_names" : target.modules}
        boot = self.get_boot_script("com_servers")
        # and build it
        return self.build_executable(target, template, arcname, boot, vars)

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

    def build_service(self, target, template, arcname):
        # services still need a little thought.  It should be possible
        # to host many modules in a single service - but pythonservice.exe
        # isn't really there yet.
        from py2exe_util import add_resource
        module_names = target.modules
        assert len(target.modules)==1, "We only support one service module"
        module_name = target.modules[0]

        vars = {"service_module_names" : target.modules}
        boot = self.get_boot_script("service")
        return self.build_executable(target, template, arcname, boot, vars)

    def build_executable(self, target, template, arcname, script, vars={}):
        # Build an executable for the target
        # template is the exe-stub to use, and arcname is the zipfile
        # containing the python modules.
        from py2exe_util import add_resource, add_icon
        if is_debug_build:
            base_d, ext_d = os.path.splitext(template)
            template_d = base_d + "_d" + ext_d
            template = template_d

        ext = os.path.splitext(template)[1]
        exe_base = target.get_dest_base()
        exe_path = os.path.join(self.dist_dir, exe_base + ext)
        # The user may specify a sub-directory for the exe - that's fine, we
        # just specify the parent directory for the .zip
        parent_levels = len(os.path.normpath(exe_base).split(os.sep))-1
        lib_leaf = self.lib_dir[len(self.dist_dir)+1:]
        relative_arcname = ((".." + os.sep) * parent_levels)
        if lib_leaf: relative_arcname += lib_leaf + os.sep
        relative_arcname += os.path.basename(arcname)

        src = os.path.join(os.path.dirname(__file__), template)
        self.copy_file(src, exe_path)

        # We create a list of code objects, and write it as a marshaled
        # stream.  The framework code then just exec's these in order.
        # First is our common boot script.
        boot = self.get_boot_script("common")
        boot_code = compile(file(boot, "U").read(),
                            os.path.abspath(boot), "exec")
        code_objects = [boot_code]
        for var_name, var_val in vars.items():
            code_objects.append(
                    compile("%s=%r\n" % (var_name, var_val), var_name, "exec")
            )
        code_object = compile(open(script, "U").read(),
                              os.path.basename(script), "exec")
        code_objects.append(code_object)
        code_bytes = marshal.dumps(code_objects)

        import struct
        si = struct.pack("iiii",
                         0x78563412, # a magic value,
                         self.optimize,
                         self.unbuffered,
                         len(code_bytes),
                         ) + relative_arcname + "\000"

        script_bytes = si + code_bytes + '\000\000'
        self.announce("add script resource, %d bytes" % len(script_bytes))
        if not self.dry_run:
            add_resource(exe_path, script_bytes, "PYTHONSCRIPT", 1, 0)
        # Handle all resources specified by the target
        bitmap_resources = getattr(target, "bitmap_resources", [])
        for bmp_id, bmp_filename in bitmap_resources:
            bmp_data = open(bmp_filename, "rb").read()
            # skip the 14 byte bitmap header.
            if not self.dry_run:
                add_resource(exe_path, bmp_data[14:], RT_BITMAP, bmp_id, False)
        icon_resources = getattr(target, "icon_resources", [])
        for ico_id, ico_filename in icon_resources:
            if not self.dry_run:
                add_icon(exe_path, ico_filename, ico_id)

        typelib = getattr(target, "typelib", None)
        if typelib is not None:
            data = open(typelib, "rb").read()
            add_resource(exe_path, data, "TYPELIB", 1, False)

        return exe_path

    def find_dependend_dlls(self, use_runw, dlls, pypath, dll_excludes):
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
        
        alldlls, warnings = bin_depends(loadpath, images, dll_excludes)
        for dll in alldlls:
            self.announce("  %s" % dll)
##XXX        alldlls.remove(self.get_exe_stub(use_runw))

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

        return py_files, extensions

    def plat_finalize(self, modules, py_files, extensions, dlls):
        # platform specific code for final adjustments to the
        # file lists
        if sys.platform == "win32":
            # pythoncom and pywintypes are imported via LoadLibrary calls,
            # help py2exe to include the dlls:
            if "pythoncom" in modules.keys():
                import pythoncom
                dlls.add(pythoncom.__file__)
            if "pywintypes" in modules.keys():
                import pywintypes
                dlls.add(pywintypes.__file__)
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
            print "creating python loader for extension '%s'" % item.__name__

        fname = os.path.basename(item.__file__)
        source = LOADER % fname
        if not self.dry_run:
            open(pathname, "w").write(source)
        else:
            return
        from modulefinder import Module
        return Module(item.__name__, pathname)

    def plat_prepare(self):
        # update the self.excludes list to exclude platform specific
        # modules
        if sys.platform == "win32":
            self.excludes += ["os2", "posix", "dos", "mac", "macfs", "macfsn",
                              "macpath", "grp",
                              "MACFS", "pwd", "MacOS", "macostools",
                              "EasyDialogs", "termios", "TERMIOS",
                              "java.lang", "org.python.core", "riscos",
                              "riscosenviron", "riscospath", "ce",
                              "os.path",
                              "Carbon.Folder", "Carbon.Folders",
                              ]
            # special dlls which must be copied to the exe_dir, not the lib_dir
            if is_debug_build:
                name = "python%d%d_d.dll" % (sys.version_info[0], sys.version_info[1])
            else:
                name = "python%d%d.dll" % (sys.version_info[0], sys.version_info[1])
            self.dlls_in_exedir = [name]
        else:
            raise DistutilsError, "Platform %s not yet implemented" % sys.platform

    def find_needed_modules(self, mf, files, modules):
        # feed Modulefinder with everything, and return it.
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
            # If modulefinder has seen a reference to the package, then
            # we prefer to believe that (imp_find_module doesn't seem to locate
            # sub-packages)
            if f in mf.modules:
                path = mf.modules[f].__path__[0]
            else:
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

    def make_lib_archive(self, zip_filename, base_dir, verbose=0,
                         dry_run=0, compression=zipfile.ZIP_STORED):
        # Like distutils "make_archive", except we can specify the
        # compression to use - default is ZIP_STORED to keep the
        # runtime performance up.
        # Also, we don't append '.zip' to the filename.
        from distutils.dir_util import mkpath
        mkpath(os.path.dirname(zip_filename), dry_run=dry_run)
        def visit (z, dirname, names):
            for name in names:
                path = os.path.normpath(os.path.join(dirname, name))
                if os.path.isfile(path):
                    z.write(path, path)

        if not dry_run:
            z = zipfile.ZipFile(zip_filename, "w",
                                compression=compression)
            save_cwd = os.getcwd()
            os.chdir(base_dir)
            os.path.walk('', visit, z)
            os.chdir(save_cwd)
            z.close()

        return zip_filename


################################################################

class FileSet:
    # A case insensitive but case preserving set of files
    def __init__(self, iterable=None):
        self._dict = {}
        if iterable is not None:
            for arg in iterable:
                self.add(arg)

    def __repr__(self):
        return "<FileSet %s at %x>" % (self._dict.values(), id(self))

    def add(self, fname):
        self._dict[fname.upper()] = fname

    def remove(self, fname):
        del self._dict[fname.upper()]

    def __contains__(self, fname):
        return fname.upper() in self._dict.keys()

    def __getitem__(self, index):
        key = self._dict.keys()[index]
        return self._dict[key]

    def __len__(self):
        return len(self._dict)

    def copy(self):
        res = FileSet()
        res._dict.update(self._dict)
        return res

# class FileSet()

def bin_depends(path, images, excluded_dlls):
    import py2exe_util
    warnings = FileSet()
    images = FileSet(images)
    dependents = FileSet()
    while images:
        for image in images.copy():
            images.remove(image)
            if not image in dependents:
                dependents.add(image)
                abs_image = os.path.abspath(image)
                loadpath = os.path.dirname(abs_image) + ';' + path
                for result in py2exe_util.depends(image, loadpath).items():
                    dll, uses_import_module = result
                    if not dll in images \
                       and not dll in dependents \
                       and not os.path.basename(dll).lower() in excluded_dlls \
                       and not isSystemDLL(dll):
                        images.add(dll)
                        if uses_import_module:
                            warnings.add(dll)
    return dependents, warnings
    
def isSystemDLL(pathname):
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

# win32com makepy helper.
def collect_win32com_genpy(path, typelibs):
    from modulefinder import Module
    import win32com, pywintypes
    from win32com.client import gencache, makepy
    old_gen_path = win32com.__gen_path__
    num = 0
    try:
        win32com.__gen_path__ = path
        win32com.gen_py.__path__ = [path]
        gencache.__init__()
        for info in typelibs:
            makepy.GenerateFromTypeLibSpec(info, bForDemand = True)
            # Now get the module, and build all sub-modules.
            mod = gencache.GetModuleForTypelib(*info)
            for clsid, name in mod.CLSIDToPackageMap.items():
                try:
                    sub_mod = gencache.GetModuleForCLSID(clsid)
                    num += 1
                    #print "", name
                except ImportError:
                    pass
        return os.path.join(path, "dicts.dat"), num
    finally:
        # restore win32com, just in case.
        win32com.__gen_path__ = old_gen_path
        win32com.gen_py.__path__ = [old_gen_path]
        gencache.__init__()

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

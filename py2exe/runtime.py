#!/usr/bin/python3.3-32
# -*- coding: utf-8 -*-
from .dllfinder import Scanner, pydll

import imp
import io
import logging
import marshal
import os
import pkgutil
import shutil
import struct
import sys
import zipfile

from .resources import UpdateResources
from .versioninfo import Version
from .icons import BuildIcons

logger = logging.getLogger("runtime")

from importlib.machinery import EXTENSION_SUFFIXES
if '.pyd' in EXTENSION_SUFFIXES:
    EXTENSION_TARGET_SUFFIX = '.pyd'
else:
    raise AssertionError
from importlib.machinery import DEBUG_BYTECODE_SUFFIXES, OPTIMIZED_BYTECODE_SUFFIXES

RT_MANIFEST = 24

class Target:
    """
    A very loosely defined "target".  We assume either a "script" or "modules"
    attribute.  Some attributes will be target specific.
    """
    # A custom requestedExecutionLevel for the User Access Control portion
    # of the manifest for the target. May be a string, which will be used for
    # the 'requestedExecutionLevel' portion and False for 'uiAccess', or a tuple
    # of (string, bool) which specifies both values. If specified and the
    # target's 'template' executable has no manifest (ie, python 2.5 and
    # earlier), then a default manifest is created, otherwise the manifest from
    # the template is copied then updated.
    uac_info = None

    def __init__(self, **kw):
        self.__dict__.update(kw)
        # If modules is a simple string, assume they meant list
        m = self.__dict__.get("modules")
        if m and isinstance(m, str):
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
            if not isinstance(r_id, int):
                # Hm, strings are also allowed as resource ids...
                raise TypeError("Resource ID must be an integer")
            if not os.path.isfile(r_filename):
                raise FileNotFoundError("Resource filename '%s' does not exist" % r_filename)

    def analyze(self, modulefinder):
        """Run modulefinder on anything that is needed for this target.

        This may be the script or one or more modules.
        """
        if hasattr(self, "script"):
            modulefinder.run_script(self.script)
        elif hasattr(self, "modules"):
            for mod in self.modules:
                modulefinder.import_hook(mod)
        else:
            raise TypeError("Don't know how to build", self)

    def __repr__(self):
        return "Target(dest_base=%r, exe_type=%r)" % (self.get_dest_base(), self.exe_type)


def fixup_targets(targets, default_attribute):
    """Fixup the targets; and ensure that the default_attribute is
    present.  Depending on the type of target, 'default_attribute' is
    "script" or "module".

    Return a list of Target instances.
    """
    if not targets:
        return []
    ret = []
    for target_def in targets:
        if isinstance(target_def, str):
            # Create a default target object, with the string as the attribute
            target = Target(**{default_attribute: target_def})
        else:
            d = getattr(target_def, "__dict__", target_def)
            if not default_attribute in d:
                raise TypeError(
                      "This target class requires an attribute '%s'" % default_attribute)
            target = Target(**d)
        target.validate()
        ret.append(target)
    return ret


class Runtime(object):
    """This class represents the Python runtime: all needed modules
    and packages.  The runtime will be written to a zip.file
    (typically named pythonxy.zip) that can be added to sys.path.
    """

    # modules which are always needed
    bootstrap_modules = {
        # Needed for Python itself:
        "codecs",
        "io",
        "encodings.*",
        "ctypes", # needed for the boot_common boot script
        }

    def __init__(self, options):
        self.options = options

        self.targets = self.options.script + self.options.service + self.options.com_servers

##         # build the executables
##         for target in dist.console:
##             dst = self.build_executable(target, self.get_console_template(),
##                                         arcname, target.script)
##             self.console_exe_files.append(dst)
##         for target in dist.windows:
##             dst = self.build_executable(target, self.get_windows_template(),
##                                         arcname, target.script)
##             self.windows_exe_files.append(dst)
##         for target in dist.service:
##             dst = self.build_service(target, self.get_service_template(),
##                                      arcname)
##             self.service_exe_files.append(dst)

        if self.options.bundle_files < 3:
            self.bootstrap_modules.add("zipextimporter")

        self.options.excludes = self.options.excludes if self.options.excludes else ()
        self.options.optimize = self.options.optimize if self.options.optimize else 0

    def analyze(self):
        logger.info("Analyzing the code")

        mf = self.mf = Scanner(excludes=self.options.excludes,
                               optimize=self.options.optimize)

        for modname in self.bootstrap_modules:
            if modname.endswith(".*"):
                self.mf.import_package(modname[:-2])
            else:
                self.mf.import_hook(modname)

        if self.options.includes:
            for modname in self.options.includes:
                mf.import_hook(modname)

        if self.options.packages:
            for modname in self.options.packages:
                mf.import_package(modname)

        for target in self.targets:
            if target.exe_type == "ctypes_comdll":
                mf.import_hook("_ctypes")
            target.analyze(mf)
            modules = getattr(target, "modules", [])
            for m in modules:
                mf.import_hook(m)

        mf.finish()

        missing, maybe = mf.missing_maybe()
        logger.info("Found %d modules, %d are missing, %d may be missing",
                    len(mf.modules), len(missing), len(maybe))

        if self.options.report:
            self.mf.report()

        elif self.options.summary:
            self.mf.report_summary()
            self.mf.report_missing()

        elif missing:
            mf.report_missing()

        errors = []
        for name, value in self.mf.get_min_bundle().items():
            if value > self.options.bundle_files:
                # warn if modules are know to work only for a minimum
                # bundle_files value
                errors.append([name, value])

        if errors:
            print("The following modules require a minimum bundle_files option,")
            print("otherwise they will not work (currently bundle_files is set to %d):"
                  % self.options.bundle_files)
            for name, value in errors:
                print("    %s: %s" % (name, value))
            print("\nPlease change the bundle_files option and run the build again.")
            print("Build failed.")
            raise SystemExit(-1)

    def build(self):
        """Build everything.
        """
        options = self.options

        destdir = options.destdir
        if not os.path.exists(destdir):
            os.mkdir(destdir)

        for i, target in enumerate(self.targets):
            # basename of the exe to create
            dest_base = target.get_dest_base()

            if target.exe_type in ("ctypes_comdll"):
                # full path to exe-file
                exe_path = os.path.join(destdir, dest_base + ".dll")
            else:
                # full path to exe-file
                exe_path = os.path.join(destdir, dest_base + ".exe")

            if os.path.isfile(exe_path):
                os.remove(exe_path)

            self.build_exe(target, exe_path, options.libname)

            if options.libname is None:
                # Put the library into the exe itself.

                # It would probably make sense to run analyze()
                # separately for each exe so that they do not contain
                # unneeded stuff (from other exes)
                self.build_archive(exe_path)

        if options.libname is not None:
            # Build a library shared by ALL exes.
            libpath = os.path.join(destdir, options.libname)
            if os.path.isfile(libpath):
                os.remove(libpath)

            if not os.path.exists(os.path.dirname(libpath)):
                os.mkdir(os.path.dirname(libpath))

            dll_bytes = pkgutil.get_data("py2exe", "resources.dll")
            with open(libpath, "wb") as ofi:
                  ofi.write(dll_bytes)
            if options.verbose:
                print("Building shared code archive '%s'." % libpath)
            # Archive is appended to resources.dll; remove the icon
            # from the dll.  The icon is only present because on some
            # systems resources otherwise cannot be updated correctly.
            self.build_archive(libpath, delete_existing_resources=True)

        self.copy_files(destdir)

        # data directories from modulefinder
        for name, (src, recursive) in self.mf._data_directories.items():
            if recursive:
                dst = os.path.join(destdir, name)
                if os.path.isdir(dst):
                    # Emit a warning?
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                raise RuntimeError("not yet supported")

        # data files from modulefinder
        for name, src in self.mf._data_files.items():
            dst = os.path.join(destdir, name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

        # other data files
        if self.options.data_files:
            for subdir, files in self.options.data_files:
                os.makedirs(os.path.join(destdir, subdir), exist_ok=True)
                for src in files:
                    dst = os.path.join(destdir, subdir)
                    shutil.copy2(src, dst)

    def get_runstub_bytes(self, target):
        from distutils.util import get_platform
        if target.exe_type in ("console_exe", "service"):
            run_stub = 'run-py%s.%s-%s.exe' % (sys.version_info[0], sys.version_info[1], get_platform())
        elif target.exe_type == "windows_exe":
            run_stub = 'run_w-py%s.%s-%s.exe' % (sys.version_info[0], sys.version_info[1], get_platform())
        elif target.exe_type == "ctypes_comdll":
            run_stub = 'run_ctypes_dll-py%s.%s-%s.dll' % (sys.version_info[0], sys.version_info[1], get_platform())
        else:
            raise ValueError("Unknown exe_type %r" % target.exe_type)
        ## if self.options.verbose:
        ##     print("Using exe-stub %r" % run_stub)
        exe_bytes = pkgutil.get_data("py2exe", run_stub)
        if exe_bytes is None:
            raise RuntimeError("run-stub not found")
        return exe_bytes

    def build_exe(self, target, exe_path, libname):
        """Build the exe-file."""
        print("Building '%s'." % exe_path)
##        logger.info("Building exe '%s'", exe_path)

        exe_bytes = self.get_runstub_bytes(target)
        with open(exe_path, "wb") as ofi:
            ofi.write(exe_bytes)

        optimize = self.options.optimize
        unbuffered = self.options.unbuffered

        script_data = self._create_script_data(target)

        if libname is None:
            zippath = b""
        else:
            zippath = libname.encode("mbcs")


        script_info = struct.pack("IIII",
                                  0x78563412,
                                  optimize if optimize is not None else 0,
                                  unbuffered if unbuffered is not None else 0,
                                  len(script_data))
        script_info += zippath + b"\0" + script_data + b"\0"

        # It seems resources must be updated in chunks if there are
        # many, otherwise EndUpdateResource will fail with
        # WindowsError 13 (invalid data)
        with UpdateResources(exe_path, delete_existing=True) as resource:
            if self.options.verbose > 1:
                print("Add resource %s/%s(%d bytes) to %s"
                      % ("PYTHONSCRIPT", 1, len(script_info), exe_path))
            resource.add(type="PYTHONSCRIPT", name=1, value=script_info)
##            # XXX testing
##            resource.add_string(1000, "foo bar")
##            resource.add_string(1001, "Hallöle €")

        with UpdateResources(exe_path, delete_existing=False) as res_writer:
            for res_type, res_name, res_data in getattr(target, "other_resources", ()):
                if res_type == RT_MANIFEST and isinstance(res_data, str):
                    res_data = res_data.encode("utf-8")
                res_writer.add(type=res_type, name=res_name, value=res_data)

            # Build and add a versioninfo resource

            # XXX better use resource.add_version(target) ???  would look nicer...
            if hasattr(target, "version"):
                def get(name):
                    return getattr(target, name, None)
                version = Version(target.version,
                                  file_description = get("description"),
                                  comments = get("comments"),
                                  company_name = get("company_name"),
                                  legal_copyright = get("copyright"),
                                  legal_trademarks = get("trademarks"),
                                  original_filename = os.path.basename(exe_path),
                                  product_name = get("product_name"),
                                  product_version = get("product_version") or target.version,
                                  internal_name = get("internal_name"),
                                  private_build = get("private_build"),
                                  special_build = get("special_build"))


                from ._wapi import RT_VERSION
                res_writer.add(type=RT_VERSION,
                             name=1,
                             value=version.resource_bytes())

        for res_type, res_name, res_data in BuildIcons(getattr(target, "icon_resources", ())):
            with UpdateResources(exe_path, delete_existing=False) as res_writer:
                res_writer.add(type=res_type, name=res_name, value=res_data)

    def build_archive(self, libpath, delete_existing_resources=False):
        """Build the archive containing the Python library.
        """
        if self.options.bundle_files <= 1:
            # Add pythonXY.dll as resource into the library file
            #
            # XXX We should add a flag to the exe so that it does not try to load pythonXY.dll
            # from the file system.
            # XXX XXX XXX
            with UpdateResources(libpath, delete_existing=delete_existing_resources) as resource:
                with open(pydll, "rb") as ifi:
                    pydll_bytes = ifi.read()
                # We do not need to replace the winver string resource
                # in the python dll since it will be loaded via
                # MemoryLoadLibrary, and so python cannot find the
                # string resources anyway.
                if self.options.verbose > 1:
                    print("Add resource %s/%s(%d bytes) to %s"
                          % (os.path.basename(pydll), 1, len(pydll_bytes), libpath))
                resource.add(type=os.path.basename(pydll), name=1, value=pydll_bytes)

        if self.options.optimize:
            bytecode_suffix = OPTIMIZED_BYTECODE_SUFFIXES[0]
        else:
            bytecode_suffix = DEBUG_BYTECODE_SUFFIXES[0]

        if self.options.compress:
            compression = zipfile.ZIP_DEFLATED
        else:
            compression = zipfile.ZIP_STORED

        # Create a zipfile and append it to the library file
        arc = zipfile.ZipFile(libpath, "a",
                              compression=compression)

        # The same modules may be in self.ms.modules under different
        # keys; we only need one of them in the archive.
        for mod in set(self.mf.modules.values()):
            if mod.__code__:
                path =mod.__dest_file__
                stream = io.BytesIO()
                stream.write(imp.get_magic())
                if sys.version_info >= (3,7,0):
                    stream.write(b"\0\0\0\0") # null flags
                stream.write(b"\0\0\0\0") # null timestamp
                stream.write(b"\0\0\0\0") # null size
                marshal.dump(mod.__code__, stream)
                arc.writestr(path, stream.getvalue())
            elif hasattr(mod, "__file__"):
                try:
                    assert mod.__file__.endswith(EXTENSION_TARGET_SUFFIX)
                except AssertionError:
                    # never put DLLs in the archive
                    continue
                if self.options.bundle_files <= 2:
                    # put .pyds into the archive
                    arcfnm = mod.__name__.replace(".", "\\") + EXTENSION_TARGET_SUFFIX
                    if self.options.verbose > 1:
                        print("Add %s to %s" % (os.path.basename(mod.__file__), libpath))
                    arc.write(mod.__file__, arcfnm)
                else:
                    # The extension modules will be copied into
                    # dlldir.  To be able to import it without dlldir
                    # being on sys.path, create a loader module and
                    # put that into the archive.
                    pydfile = mod.__name__ + EXTENSION_TARGET_SUFFIX
                    if self.options.verbose > 1:
                        print("Add Loader for %s to %s" % (os.path.basename(mod.__file__), libpath))
                    loader = LOAD_FROM_DIR.format(pydfile)

                    code = compile(loader, "<loader>", "exec",
                                   optimize=self.options.optimize)
                    if hasattr(mod, "__path__"):
                        path = mod.__name__.replace(".", "\\") + "\\__init__" + bytecode_suffix
                    else:
                        path = mod.__name__.replace(".", "\\") + bytecode_suffix
                    stream = io.BytesIO()
                    stream.write(imp.get_magic())
                    if sys.version_info >= (3,7,0):
                        stream.write(b"\0\0\0\0") # null flags
                    stream.write(b"\0\0\0\0") # null timestamp
                    stream.write(b"\0\0\0\0") # null size
                    marshal.dump(code, stream)
                    arc.writestr(path, stream.getvalue())
            elif mod.__spec__ is not None and mod.__spec__.origin == 'namespace':
                # implicit namespace packages, create empty __init__.py for zipimport
                if self.options.verbose > 1:
                    print("Add empty __init__ for implicit namespace package %s to %s" % (mod.__name__, libpath))
                path = mod.__name__.replace(".", "\\") + "\\__init__" + bytecode_suffix
                code = compile(r"", path, "exec", optimize=self.options.optimize)
                stream = io.BytesIO()
                stream.write(imp.get_magic())
                if sys.version_info >= (3,7,0):
                    stream.write(b"\0\0\0\0") # null flags
                stream.write(b"\0\0\0\0") # null timestamp
                stream.write(b"\0\0\0\0") # null size
                marshal.dump(code, stream)
                arc.writestr(path, stream.getvalue())

        if self.options.bundle_files == 0:
            # put everything into the arc
            files = self.mf.all_dlls()
        elif self.options.bundle_files in (1, 2):
            # put only extension dlls into the arc
            files = self.mf.extension_dlls()
        else:
            arc.close()
            return

        for src in files:
            if self.options.verbose > 1:
                print("Add DLL %s to %s" % (os.path.basename(src), libpath))
            arc.write(src, os.path.basename(src))

        arc.close()

    def copy_files(self, destdir):
        """Copy files (pyds, dlls, depending on the bundle_files value,
        into the dist resp. library directory.
        """
        if self.options.libname is not None:
            libdir = os.path.join(destdir, os.path.dirname(self.options.libname))
        else:
            libdir = destdir

        if self.options.bundle_files >= 2:
            # Python dll is not bundled; copy it into destdir
            dst = os.path.join(destdir, os.path.basename(pydll))
            if self.options.verbose:
                print("Copy %s to %s" % (pydll, destdir))
            shutil.copy2(pydll, dst)
#             with UpdateResources(dst, delete_existing=False) as resource:
#                 resource.add_string(1000, "py2exe")

        if self.options.bundle_files == 3:
            # copy extension modules; they go to libdir
            for mod in self.mf.modules.values():
                if mod.__code__:
                    # nothing to do for python modules.
                    continue
                if hasattr(mod, "__file__"):
                    try:
                        assert mod.__file__.endswith(EXTENSION_TARGET_SUFFIX)
                    except AssertionError:
                        # check if the DLL will be copied afterwards
                        assert (mod.__file__ in self.mf.real_dlls() or mod.__file__ in  self.mf.extension_dlls())
                        continue
                    pydfile = mod.__name__ + EXTENSION_TARGET_SUFFIX

                    dst = os.path.join(libdir, pydfile)
                    if self.options.verbose:
                        print("Copy %s to %s" % (mod.__file__, dst))
                    shutil.copy2(mod.__file__, dst)

        if self.options.bundle_files < 1:
            return

        for src in self.mf.real_dlls():
            # Strange, but was tested with numpy built with
            # libiomp5md.dll...
            if self.options.bundle_files == 3:
                extdlldir = libdir
            else:
                extdlldir = destdir
            if self.options.verbose:
                print("Copy DLL %s to %s" % (src, extdlldir))
            shutil.copy2(src, extdlldir)

        # lib files from modulefinder
        for name, src in self.mf._lib_files.items():
            if self.options.bundle_files == 3:
                extdlldir = libdir
            else:
                extdlldir = destdir
            dst = os.path.join(extdlldir, name)
            # extdlldir can point to a subfolder if it was defined from the `zipfile` option
            if os.path.dirname(extdlldir):
                os.makedirs(os.path.dirname(extdlldir), exist_ok=True)
            else:
                os.makedirs(extdlldir, exist_ok=True)
            if self.options.verbose:
                print("Copy lib file %s to %s" % (src, extdlldir))
            if os.path.sep in name:
                # name can contain subfolders, if so we need to create them
                os.makedirs(os.path.join(extdlldir, os.path.dirname(name)), exist_ok=True)
            shutil.copy2(src, dst)

        if self.options.bundle_files == 3:
            # extension dlls go to libdir
            for src in self.mf.extension_dlls():
                if self.options.verbose:
                    print("Copy ExtensionDLL %s to %s" % (src, libdir))
                shutil.copy2(src, libdir)

    def _create_script_data(self, target):
        # We create a list of code objects, and return it as a
        # marshaled stream.  The framework code then just exec's these
        # in order.

        ## # First is our common boot script.
        ## boot = self.get_boot_script("common")
        ## boot_code = compile(file(boot, "U").read(),
        ##                     os.path.abspath(boot), "exec")
        ## code_objects = [boot_code]
        ## for var_name, var_val in vars.iteritems():
        ##     code_objects.append(
        ##             compile("%s=%r\n" % (var_name, var_val), var_name, "exec")
        ##     )
        ## if self.custom_boot_script:
        ##     code_object = compile(file(self.custom_boot_script, "U").read() + "\n",
        ##                           os.path.abspath(self.custom_boot_script), "exec")
        ##     code_objects.append(code_object)
        ## code_bytes = marshal.dumps(code_objects)

        code_objects = []

        # sys.executable has already been set in the run-stub

        # XXX should this be done in the exe-stub?
        code_objects.append(
            compile("import os, sys; sys.base_prefix = sys.prefix = os.path.dirname(sys.executable); del os, sys",
                    "<bootstrap2>", "exec",
                    optimize=self.options.optimize))

        if self.options.bundle_files < 3:
            # XXX do we need this one?
            ## obj = compile("import sys, os; sys.path.append(os.path.dirname(sys.path[0])); del sys, os",
            ##               "<bootstrap>", "exec")
            ## code_objects.append(obj)
            obj = compile("import zipextimporter; zipextimporter.install(); del zipextimporter",
                          "<install zipextimporter>", "exec",
                          optimize=self.options.optimize)
            code_objects.append(obj)

        for text in self.mf._boot_code:
            code_objects.append(
                compile(text,
                        "<boot hacks>", "exec",
                        optimize=self.options.optimize))

        if target.exe_type == "service":

            cmdline_style = getattr(target, "cmdline_style", "py2exe")
            if cmdline_style not in ["py2exe", "pywin32", "custom"]:
                raise RuntimeError("cmdline_handler invalid")

            # code for services
            # cmdline_style is one of:
            # py2exe
            # pywin32
            # custom
            code_objects.append(
                compile("cmdline_style = %r; service_module_names = %r" % (cmdline_style, target.modules,),
                        "<service_info>", "exec",
                        optimize=self.options.optimize))

            boot_code = compile(pkgutil.get_data("py2exe", "boot_service.py"),
                                "boot_service.py", "exec",
                                optimize=self.options.optimize)
            code_objects.append(boot_code)

        elif target.exe_type in ("console_exe", "windows_exe"):
            boot_code = compile(pkgutil.get_data("py2exe", "boot_common.py"),
                                "boot_common.py", "exec",
                                optimize=self.options.optimize)

            code_objects.append(boot_code)

            with open(target.script, "rb") as script_file:
                code_objects.append(
                    compile(script_file.read() + b"\n",
                            os.path.basename(target.script), "exec",
                            optimize=self.options.optimize))

        elif target.exe_type == "ctypes_comdll":
            code_objects.append(
                compile("com_module_names = %r" % target.modules,
                        "com_module_names", "exec",
                        optimize=self.options.optimize))

            boot_code = compile(pkgutil.get_data("py2exe", "boot_ctypes_com_server.py"),
                                "boot_ctypes_com_server.py", "exec",
                                optimize=self.options.optimize)

            code_objects.append(boot_code)
        else:
            raise RuntimeError("target_type '%s' not yet supported")

        return marshal.dumps(code_objects)

################################################################

LOAD_FROM_DIR = r"""\
def __load():
    import imp, os
    dllpath = os.path.join(os.path.dirname(__loader__.archive), r'{0}')
    try:
        mod = imp.load_dynamic(__name__, dllpath)
    except ImportError as details:
        raise ImportError('(%s) %r' % (details, dllpath)) from None
    mod.frozen = 1
__load()
del __load
"""

################################################################

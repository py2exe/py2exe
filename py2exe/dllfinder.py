#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""dllfinder
"""
from . import _wapi
from . import pescan
import collections
from importlib.machinery import EXTENSION_SUFFIXES
import os

import platform
import sys

from fnmatch import fnmatch

from cachetools import cached, LFUCache

from . mf34 import ModuleFinder
from . import hooks

WINDOWSCRTPATTERN = "api-ms-win-*.dll"
VCRUNTIMEPATTERN = "vcruntime*.dll"

################################
# XXX Move these into _wapi???
_buf = _wapi.create_unicode_buffer(260)

_wapi.GetWindowsDirectoryW(_buf, len(_buf))
windir = _buf.value.lower()

_wapi.GetSystemDirectoryW(_buf, len(_buf))
sysdir = _buf.value.lower()

_wapi.GetModuleFileNameW(sys.dllhandle, _buf, len(_buf))
pydll = _buf.value.lower()

def SearchPath(imagename, path=None):
    pfile = _wapi.c_wchar_p()
    if _wapi.SearchPathW(path,
                         imagename,
                         None,
                         len(_buf),
                         _buf,
                         pfile):
        return _buf.value
    return None

# global accessed by BindImageEx callback
TEMP = set()

################################

class DllFinder:

    def __init__(self):
        # _loaded_dlls contains ALL dlls that are bound, this includes
        # the loaded extension modules; maps lower case basename to
        # full pathname.
        self._loaded_dlls = {}

        # _dlls contains the full pathname of the dlls that
        # are NOT considered system dlls.
        #
        # The pathname is mapped to a set of modules/dlls that require
        # this dll. This allows to find out WHY a certain dll has to
        # be included.
        self._dlls = collections.defaultdict(set)

    def _add_dll(self, path):
        self._dlls[path]
        self.import_extension(path)

    def import_extension(self, pyd, callers=None):
        """Add an extension module and scan it for dependencies.

        """
        todo = {pyd} # todo contains the dlls that we have to examine

        while todo:
            dll = todo.pop() # get one and check it
            if dll in self._loaded_dlls:
                continue
            for dep_dll in self.bind_image(dll):
                if dep_dll in self._loaded_dlls:
                    continue
                dll_type = self.determine_dll_type(dep_dll)
                if dll_type is None:
                    continue
                ## if dll_type == "EXT":
                ##     print("EXT", dep_dll)
                ## elif dll_type == "DLL":
                ##     print("DLL", dep_dll)
                todo.add(dep_dll)
                self._dlls[dep_dll].add(dll)

    @cached(cache=LFUCache(maxsize=128))
    def bind_image(self, imagename):
        """Call BindImageEx and collect all dlls that are bound.
        """
        if platform.architecture()[0]=="32bit":
            pth = ";".join([p for p in os.environ["PATH"].split(';') if not "intel64_win" in p])
        elif platform.architecture()[0]=="64bit":
            pth = ";".join([p for p in os.environ["PATH"].split(';') if not "ia32_win" in p])
        else:
            pth = os.environ["PATH"]

        #import pdb;pdb.set_trace()
        path = ";".join([os.path.dirname(imagename),
                         os.path.dirname(sys.executable),
                         pth])

        # apply path
        old_path = os.environ["PATH"]
        assert isinstance(path, str)
        os.environ["PATH"] = path

        # scan path with pefile first, append found directories to path
        pefile_dlls = pescan.find_loaded_dlls(imagename)

        bound = set()
        for lib in pefile_dlls:
            pt = self.search_path(lib, path)
            if pt is not None:
                bound.add(pt)

        # probe results with BindImageEx
        result = set()

        for name in bound:
            ret = 0
            TEMP.clear()

            @_wapi.PIMAGEHLP_STATUS_ROUTINE
            def status_routine(reason, img_name, dllname, va, parameter):
                if reason == _wapi.BindImportModule: # 5
                    if img_name.decode("mbcs") == name:
                        # name binds to dllname
                        dllname = self.search_path(dllname.decode("mbcs"), path)
                        TEMP.add(dllname)
                return True

            # BindImageEx uses the PATH environment variable to find
            # dependend dlls; set it to our changed PATH:
            ret =  _wapi.BindImageEx(_wapi.BIND_ALL_IMAGES
                            | _wapi.BIND_CACHE_IMPORT_DLLS
                            | _wapi.BIND_NO_UPDATE,
                            name.encode("mbcs"),
                            None,
                            ##path.encode("mbcs"),
                            None,
                            status_routine)

            if ret == 1:
                self._loaded_dlls[os.path.basename(name).lower()] = name
                result.add(name)
                result.update(TEMP)

        # Be a good citizen and cleanup:
        os.environ["PATH"] = old_path

        return result

    def determine_dll_type(self, imagename):
        """determine_dll_type must be called with a full pathname.

        For any dll in the Windows or System directory or any
        subdirectory thereof return None, except when the dll binds to
        or IS the current python dll. Additionally, return None for DLLs
        that belong to either the Visual C++ redistributable or the
        Universal C Runtime.

        Return "DLL" when the image binds to the python dll, return
        None when the image is in the windows or system directory or belongs
        to a windows framework, return "EXT" otherwise.
        """
        fnm = imagename.lower()

        if fnm == pydll.lower():
            return "DLL"

        deps = self.bind_image(imagename)
        if pydll in [d.lower() for d in deps]:
            return "EXT"

        if fnm.startswith(windir + os.sep) or \
            fnm.startswith(sysdir + os.sep) or \
            fnmatch(os.path.basename(fnm), WINDOWSCRTPATTERN) or \
            fnmatch(os.path.basename(fnm), VCRUNTIMEPATTERN):
            return None

        return "DLL"

    def search_path(self, imagename, path):
        """Find an image (exe or dll) on the PATH."""
        if imagename.lower() in self._loaded_dlls:
            return self._loaded_dlls[imagename.lower()]
        # SxS files (like msvcr90.dll or msvcr100.dll) are only found in
        # the SxS directory when the PATH is NULL.
        if path is not None:
            found = SearchPath(imagename)
            if found is not None:
                return found
        return SearchPath(imagename, path)

    def all_dlls(self):
        """Return a set containing all dlls that are needed,
        except the python dll.
        """
        return {dll for dll in self._dlls
                if dll.lower() != pydll.lower()}

    def extension_dlls(self):
        """Return a set containing only the extension dlls that are
        needed.
        """
        return {dll for dll in self._dlls
                if "EXT" == self.determine_dll_type(dll)}

    def real_dlls(self):
        """Return a set containing only the dlls that do not bind to
        the python dll.
        """
        return {dll for dll in self._dlls
                if "DLL" == self.determine_dll_type(dll)
                and dll.lower() != pydll.lower()}

################################################################

class Scanner(ModuleFinder):
    """A ModuleFinder subclass which allows to find binary
    dependencies.
    """
    def __init__(self, path=None, verbose=0, excludes=[], optimize=0):
        super().__init__(path, verbose, excludes, optimize)
        self.dllfinder = DllFinder()
        self._data_directories = {}
        self._data_files = {}
        self._lib_files = {}
        self._min_bundle = {}
        self._import_package_later = []
        self._safe_import_hook_later = []
        self._boot_code = []
        hooks.init_finder(self)

    def add_bootcode(self, code):
        """Add some code that the exe will execute when bootstrapping."""
        self._boot_code.append(code)

    def set_min_bundle(self, name, value):
        self._min_bundle[name] = value

    def get_min_bundle(self):
        return self._min_bundle

    def hook(self, mod):
        hookname = "hook_%s" % mod.__name__.replace(".", "_")
        mth = getattr(hooks, hookname, None)
        if mth:
            mth(self, mod)

    def _add_module(self, name, mod):
        self.hook(mod)
        super()._add_module(name, mod)
        if hasattr(mod, "__file__") \
               and mod.__file__.endswith(tuple(EXTENSION_SUFFIXES)):
            callers = {self.modules[n]
                       for n in self._depgraph[name]
                       # self._depgraph can contain '-' entries!
                       if n in self.modules}
            self._add_pyd(mod.__file__, callers)

    def _add_pyd(self, name, callers):
        self.dllfinder.import_extension(name, callers)

##    def required_dlls(self):
##        return self.dllfinder.required_dlls()
    def all_dlls(self):
        return self.dllfinder.all_dlls()

    def real_dlls(self):
        return self.dllfinder.real_dlls()

    def extension_dlls(self):
        return self.dllfinder.extension_dlls()

    def add_datadirectory(self, name, path, recursive):
        self._data_directories[name] = (path, recursive)

    def add_datafile(self, name, path):
        self._data_files[name] = path

    def add_dll(self, path):
        self.dllfinder._add_dll(path)

    ## def report_dlls(self):
    ##     import pprint
    ##     pprint.pprint(set(self.dllfinder.required_dlls()))
    ##     pprint.pprint(set(self.dllfinder.system_dlls()))

    def import_package_later(self, package):
        # This method can be called from hooks to add additional
        # packages.  It is called BEFORE a module is imported
        # completely!
        self._import_package_later.append(package)

    def add_libfile(self, name, path):
        self._lib_files[name] = path

    def safe_import_hook_later(self, name,
                               caller=None,
                               fromlist=(),
                               level=0):
        # This method can be called from hooks to add additional
        # packages.  It is called BEFORE a module is imported
        # completely!
        self._safe_import_hook_later.append((name, caller, fromlist, level))

    def finish(self):
        while self._import_package_later:
            pkg = self._import_package_later.pop()
            self.import_package(pkg)
        while self._safe_import_hook_later:
            args = self._safe_import_hook_later.pop()
            name, caller, fromlist, level = args
            self.safe_import_hook(name,
                                  caller=caller,
                                  fromlist=fromlist,
                                  level=level)

################################################################

if __name__ == "__main__":
    # test script and usage example
    #
    # Should we introduce an 'offical' subclass of ModuleFinder
    # and DllFinder?

    scanner = Scanner()
    scanner.import_package("numpy")
    print(scanner.all_dlls())

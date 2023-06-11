r"""zipextimporter - an importer which can import extension modules
from zipfiles without unpacking them to the file system.

This file and _memimporter.pyd is part of the py2exe package.

Overview
========

zipextimporter.py contains the ZipExtImporter class which allows to
load Python binary extension modules contained in a zip.archive,
without unpacking them to the file system.

Call the zipextimporter.install() function to install the import hook,
add a zip-file containing .pyd or .dll extension modules to sys.path,
and import them.

It uses the _memimporter extension which uses code from Joachim
Bauch's MemoryModule library.  This library emulates the win32 api
function LoadLibrary.

Sample usage
============

You have to prepare a zip-archive 'lib.zip' containing
your Python's _socket.pyd for this example to work.

>>> import zipextimporter
>>> zipextimporter.install()
>>> import sys
>>> sys.path.insert(0, "lib.zip")
>>> import _socket
>>> print(_socket)
<module '_socket' from 'lib.zip\_socket.pyd'>
>>> _socket.__file__
'lib.zip\\_socket.pyd'
>>> _socket.__loader__
<ZipExtensionImporter object 'lib.zip'>
>>> # Reloading also works correctly:
>>> _socket is reload(_socket)
True
>>>

"""
import sys
from zipimport import *
from _frozen_importlib import ModuleSpec, spec_from_loader
from _frozen_importlib_external import EXTENSION_SUFFIXES

# _memimporter is a module built into the py2exe runstubs.
import _memimporter


__all__ = ["ZipExtensionImporter"]


# Makes order as same as import from Non-Zip.
_searchorder = (
    *[(f"\\__init__{suffix}", True, True) for suffix in EXTENSION_SUFFIXES],
    ("\\__init__.pyc", False, True),
    ("\\__init__.py", False, True),
    *[(suffix, True, False) for suffix in EXTENSION_SUFFIXES],
    (".pyc", False, False),
    (".py", False, False),
)
# Handle pywin32 DLLs.
_names_pywin32 = frozenset(["pywintypes", "pythoncom"])
_searchorder_pywin32 = (
    *_searchorder[:-2],
    (f"%d%d{'_d.pyd' in EXTENSION_SUFFIXES and '_d' or ''}.dll"
            % sys.version_info[:2], True, False),
    *_searchorder[-2:],
)


class _ModuleInfo:
    __slots__ = ("path", "is_ext", "is_package")
    def __init__(self, *args):
        self.path, self.is_ext, self.is_package = args


# Return some information about a module.
def _get_module_info(self, fullname, *, _raise=False, _tempcache=[None, None]):
    key, mi = _tempcache
    if key == (fullname, self.archive):
        return mi
    name = fullname.rpartition(".")[2]
    if name in _names_pywin32:
        searchorder = _searchorder_pywin32
    else:
        searchorder = _searchorder
    _path = self.prefix + name
    for suffix, is_ext, is_package in searchorder:
        path = _path + suffix
        if path in self._files:
            if is_ext:
                _verbose_msg("# zipextimporter: "
                            f"found {path} in zipfile {self.archive}", 2)
            mi = _ModuleInfo(f"{self.archive}\\{path}", is_ext, is_package)
            _tempcache[:] = (fullname, self.archive), mi
            return mi
    if _raise:
        raise ZipImportError(f"can't find module {fullname!r}", name=fullname)


# Return the path if it represent a directory.
def _get_dir_path(self, fullname):
    path = self.prefix + fullname.rpartition(".")[2]
    if f"{path}\\" in self._files:
        return f"{self.archive}\\{path}"


# Does this specification represent an extension module?
def _is_ext(self, spec):
    if isinstance(spec.origin, str):
        return not spec.origin.endswith((".py", ".pyc"))
    return _get_module_info(self, spec.name, _raise=True).is_ext


class ZipExtensionImporter(zipimporter):
    __doc__ = zipimporter.__doc__.replace("zipimporter", "ZipExtensionImporter")

    if hasattr(zipimporter, "find_loader"):
        def find_loader(self, fullname, path=None):
            mi = _get_module_info(self, fullname)
            if mi is None:
                dirpath = _get_dir_path(self, fullname)
                if dirpath:
                    return None, [dirpath]
                return None, []
            return self, []

    if hasattr(zipimporter, "find_spec"):
        def find_spec(self, fullname, target=None):
            mi = _get_module_info(self, fullname)
            if mi is None:
                dirpath = _get_dir_path(self, fullname)
                if dirpath:
                    spec = ModuleSpec(fullname, None)
                    spec.submodule_search_locations = [dirpath]
                    return spec
                return None
            if mi.is_ext:
                spec = ModuleSpec(fullname, self, origin=mi.path)
                if mi.is_package:
                    spec.submodule_search_locations = [mi.path.rpartition("\\")[0]]
            else:
                spec = spec_from_loader(fullname, self, is_package=mi.is_package)
            return spec

    if hasattr(zipimporter, "load_module"):
        def load_module(self, fullname):
            # Will never enter here, beacuse of defined `exec_module` method
            mi = _get_module_info(self, fullname, _raise=True)
            if not mi.is_ext:
                return super().load_module(fullname)

            # Will never enter here, raise error for developers
            raise NotImplementedError(
                    "load_module() is not implemented for extension modules, "
                    "use create_module() & exec_module() instead.")

    def create_module(self, spec):
        fullname = spec.name
        if not _is_ext(self, spec):
            if hasattr(zipimporter, "create_module"):
                return super().create_module(spec)
            else:
                return super().load_module(fullname)

        spec._set_fileattr = True  # has_location, use for reload

        # PEP 489 multi-phase initialization / Export Hook Name
        name = fullname.rpartition(".")[2]
        try:
            name.encode("ascii")
        except UnicodeEncodeError:
            initname = "PyInitU_" + name.encode("punycode") \
                                        .decode("ascii").replace("-", "_")
        else:
            initname = "PyInit_" + name

        mod = _memimporter.import_module(fullname, spec.origin, initname,
                                         self.get_data, spec)
        _verbose_msg(f"import {fullname} # loaded from zipfile {self.archive}")
        return mod

    def exec_module(self, module):
        if hasattr(zipimporter, "exec_module"):
            if _is_ext(self, module.__spec__):
                # All has been done in create_module(),
                # also skip importlib.reload()
                pass
            else:
                super().exec_module(module)

    def get_code(self, fullname):
        mi = _get_module_info(self, fullname, _raise=True)
        if not mi.is_ext:
            return super().get_code(fullname)

    def get_source(self, fullname):
        mi = _get_module_info(self, fullname, _raise=True)
        if not mi.is_ext:
            return super().get_source(fullname)

    def get_filename(self, fullname):
        mi = _get_module_info(self, fullname, _raise=True)
        return mi.path

    def is_package(self, fullname):
        mi = _get_module_info(self, fullname, _raise=True)
        return mi.is_package

    def __repr__(self):
        return f'<{self.__class__.__name__} object "{self.archive}\\{self.prefix}">'


def install():
    "Install the zipextimporter to `sys.path_hooks`."
    for importer in sys.path_hooks:
        if isinstance(importer, type) and issubclass(importer, ZipExtensionImporter):
            if importer is not ZipExtensionImporter:
                import _warnings
                _warnings.warn("Ignore zipextimporter.install(), because there "
                               "is a sub-class of ZipExtensionImporter which "
                               "has already been installed.",
                               category=RuntimeWarning, stacklevel=2)
            return
    try:
        i = sys.path_hooks.index(zipimporter)
    except ValueError:
        sys.path_hooks.insert(0, ZipExtensionImporter)
    else:
        sys.path_hooks[i] = ZipExtensionImporter
    sys.path_importer_cache.clear()
    ## # Not sure if this is needed...
    ## import importlib
    ## importlib.invalidate_caches()


verbose = sys.flags.verbose

def _verbose_msg(msg, verbosity=1):
    if max(verbose, sys.flags.verbose) >= verbosity:
        print(msg, file=sys.stderr)

def set_verbose(i):
    "Set verbose, the argument as same as built-in function int's."
    global verbose
    verbose = int(i)

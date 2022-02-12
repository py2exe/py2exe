from .vendor.modulefinder import ModuleFinder as PythonMF

import importlib.util

from importlib.machinery import DEBUG_BYTECODE_SUFFIXES, OPTIMIZED_BYTECODE_SUFFIXES

class Module:
    """Represents a Python module.

    These attributes are set, depending on the loader:

    __code__: the code object provided by the loader; can be None.

    __file__: The path to where the module data is stored (not set for
              built-in or frozen modules).

    __globalnames__: a set containing the global names that are defined.

    __loader__: The loader for this module.

    __name__: The name of the module.

    __optimize__: Optimization level for the module's byte-code.

    __package__: The parent package for the module/package. If the
                 module is top-level then it has a value of the empty
                 string.

    __path__: A list of strings specifying the search path within a
              package. This attribute is not set on modules.

    __source__: a property that gives access to the source code (if
                the __loader__ provides it, not for builtin or
                extension modules)
    """

    def __init__(self, name, file=None, path=None, optimize=0):
        self.__name__ = name
        self.__file__ = file
        self.__path__ = path
        self.__code__ = None

        self.__code_object__ = None

        self.__optimize__ = optimize

        # The set of global names that are assigned to in the module.
        # This includes those names imported through starimports of
        # Python modules.
        self.globalnames = {}
        # The set of starimports this module did that could not be
        # resolved, ie. a starimport from a non-Python module.
        self.starimports = {}

        if getattr(self, '__package__', None) is None:
            try:
                self.__package__ = self.__name__
                if self.__path__ is None:
                    self.__package__ = self.__package__.rpartition('.')[0]
            except AttributeError:
                pass

    @property
    def __spec__(self):
        try:
            spec = importlib.util.find_spec(self.__name__)
        except:
            spec = None
        return spec

    @property
    def __loader__(self):
        try:
            loader = self.__spec__.loader
        except AttributeError as e:
            loader = None
            print(e)
            print(self)
            print(self.__name__)
            print(self.__spec__)
            print(self.__path__)
            print(self.__file__)
            raise
        return loader

    @property
    def __dest_file__(self):
        """Gets the destination path for the module that will be used at compilation time."""
        if self.__optimize__:
            bytecode_suffix = OPTIMIZED_BYTECODE_SUFFIXES[0]
        else:
            bytecode_suffix = DEBUG_BYTECODE_SUFFIXES[0]
        if self.__path__ is not None:
            return self.__name__.replace(".", "\\") + "\\__init__" + bytecode_suffix
        else:
            return self.__name__.replace(".", "\\") + bytecode_suffix

    @property
    def __source__(self):
        return self.__loader__.get_source(self.__name__)

    def __repr__(self):
        s = "Module(%r" % (self.__name__,)
        if self.__file__ is not None:
            s = s + ", %r" % (self.__file__,)
        if self.__path__ is not None:
            s = s + ", %r" % (self.__path__,)
        s = s + ")"
        return s

    def get_code_runtime(self):
        return self.__code_object__ if self.__code_object__ is not None else self.__code__


class ModuleFinder(PythonMF):
    def __init__(self, path=None, verbose=0, excludes=None, ignores=None, optimize=0, replace_paths=None):
        super().__init__(path=path, debug=verbose, excludes=excludes, replace_paths=replace_paths)

        self._verbose = verbose
        self.ignores = ignores if ignores is not None else []
        self._optimize = optimize

    def _add_module(self, name, mod):
        self.modules[name] = mod

    def add_module(self, fqname, file=None, path=None):
        if fqname in self.modules:
            return self.modules[fqname]
        m = Module(fqname, file, path, optimize=self._optimize)
        self._add_module(fqname, m)
        return m

    def ignore(self, name):
        """If the module or package with the given name is not found,
        don't record this as an error.  If is is found, however,
        include it.
        """
        self.ignores.append(name)

    def import_package(self, name):
        """Import a complete package.

        """
        self.import_hook(name,  None, ["*"])

    def missing(self):
        """Return a set of modules that appear to be missing. Use
        any_missing_maybe() if you want to know which modules are
        certain to be missing, and which *may* be missing.

        """
        missing, _ = self.any_missing_maybe()
        return missing

    def report_missing(self):
        """Print a report to stdout, listing those modules that are
        missing.

        """
        missing, maybe = self.any_missing_maybe()
        print()
        print("  %-35s" % ("%d missing Modules" % len(missing)))
        print("  %-35s" % "------------------")
        for name in missing:
            mods = sorted(self.badmodules[name].keys())
            print("? %-35s imported from %s" % (name, ", ".join(mods)))

        # Print modules that may be missing, but then again, maybe not...
        if maybe:
            print()
            print("Submodules that appear to be missing, but could also be", end=' ')
            print("global names in the parent package:")
            print("  %-35s" %
                  "-----------------------------------------"
                  "----------------------------------------------------")
            for name in maybe:
                mods = sorted(self.badmodules[name].keys())
                print("? %-35s imported from %s" % (name, ", ".join(mods)))

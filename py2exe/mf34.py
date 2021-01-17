#!/usr/bin/python3.4
# -*- coding: utf-8 -*-
"""ModuleFinder based on importlib
"""

from collections import defaultdict
import dis
import importlib
import importlib.machinery
import os
import pkgutil
import struct
import sys
import textwrap
import warnings
from importlib.machinery import DEBUG_BYTECODE_SUFFIXES, OPTIMIZED_BYTECODE_SUFFIXES

LOAD_CONST = dis.opname.index('LOAD_CONST')
IMPORT_NAME = dis.opname.index('IMPORT_NAME')
STORE_NAME = dis.opname.index('STORE_NAME')
STORE_GLOBAL = dis.opname.index('STORE_GLOBAL')
EXTENDED_ARG = dis.opname.index('EXTENDED_ARG')
STORE_OPS = [STORE_NAME, STORE_GLOBAL]
HAVE_ARGUMENT = dis.HAVE_ARGUMENT


class ModuleFinder:
    def __init__(self, path=None, verbose=0, excludes=None, optimize=0,
                 ignores=None):
        self.excludes = list(excludes) if excludes is not None else []
        self.ignores = ignores if ignores is not None else []
        self.path = path
        self._optimize = optimize
        self._verbose = verbose
        self.modules = {}
        self.badmodules = set()
        self.__last_caller = None
        self._depgraph = defaultdict(set)
        self._indent = ""
        self._package_paths = defaultdict(list)


    def add_packagepath(self, packagename, path):
        """ModuleFinder can not handle __path__ modifications packages
        make at runtime.

        This method registers extra paths for a package.
        """
        self._package_paths[packagename].append(path)


    def run_script(self, path):
        """Run a script: scan it for dependencies, but do NOT
        add it the self.modules.
        """
        assert "__SCRIPT__" not in sys.modules
        ldr = importlib.machinery.SourceFileLoader("__SCRIPT__", path)
        spec = importlib.machinery.ModuleSpec("__SCRIPT__", ldr)
        mod = Module(spec, "__SCRIPT__", self._optimize)
        # Do NOT add it...
        # self._add_module("__SCRIPT__", mod)
        self._scan_code(mod.__code__, mod)

    def import_package(self, name):
        """Import a complete package.

        """
        self.import_hook(name)
        package = self.modules[name]
        if not hasattr(package, "__path__"):
            # Hm, should we raise ImportError instead?
            raise TypeError("{0} is not a package".format(name))
        for finder, modname, ispkg in pkgutil.iter_modules(package.__path__):
            self.safe_import_hook("%s.%s" % (name, modname))
            if ispkg:
                self.import_package("%s.%s" % (name, modname))


    def import_hook(self, name, caller=None, fromlist=(), level=0):
        """Import a module.

        The 'caller' argument is used to infer where the import is
        occuring from to handle relative imports. The 'fromlist'
        argument specifies what should exist as attributes on the
        module being imported (e.g. ``from module import
        <fromlist>``).  The 'level' argument represents the package
        location to import from in a relative import (e.g. ``from
        ..pkg import mod`` would have a 'level' of 2).

        """
        self.__old_last_caller = self.__last_caller
        self.__last_caller = caller

        try:
            if level == 0:
                module = self._gcd_import(name)
            else:
                package = self._calc___package__(caller)
                module = self._gcd_import(name, package, level)
            if fromlist:
                self._handle_fromlist(module, fromlist, caller)
        finally:
            self.__last_caller = self.__old_last_caller


    def safe_import_hook(self, name, caller=None, fromlist=(), level=0):
        """Wrapper for import_hook() that catches ImportError.

        """
        INDENT = "  "
        self._info(name, caller, fromlist, level)
        self._indent = self._indent + INDENT
        try:
            self.import_hook(name, caller, fromlist, level)
        except ImportError:
            if self._verbose > 1:
                print("%s# -> ImportError" % self._indent[:-len(INDENT)])
        finally:
            self._indent = self._indent[:-len(INDENT)]


    def _info(self, name, caller, fromlist, level):
        """Print the call as a Python import statement, indented.

        """
        if self._verbose == 0:
            return
        if caller:
            caller_info = " # in %s" % caller.__name__
        else:
            caller_info = ""

        if level == 0:
            if fromlist:
                text = "%sfrom %s import %s" % (self._indent, name,
                                                ", ".join(fromlist)) + caller_info
            else:
                text = "%simport %s" % (self._indent, name) + caller_info
        elif name:
            text = "%sfrom %s import %s" % (self._indent, "."*level + name,
                                            ", ".join(fromlist)) + caller_info
        else:
            text = "%sfrom %s import %s" % (self._indent, "."*level,
                                            ", ".join(fromlist)) + caller_info
        print(text)


    def _handle_fromlist(self, mod, fromlist, caller):
        """handle the fromlist.

        Names on the fromlist can be modules or global symbols.
        """
        for x in fromlist:
            if x == "*":
                if caller is not None:
                    if mod.__code__ is None:
                        # 'from <mod> import *' We have no information
                        # about the symbols that are imported from
                        # extension, builtin, or frozen modules. Put a '*'
                        # symbol into __globalnames__ so that we can later
                        # use it in report_missing().
                        caller.__globalnames__.add("*")
                    for n in mod.__globalnames__:
                        caller.__globalnames__.add(n)
                continue
            if hasattr(mod, x):
                continue # subpackage already loaded
            if x in mod.__globalnames__:
                continue
            if hasattr(mod, "__path__"):
                try:
                    self._gcd_import('{}.{}'.format(mod.__name__, x))
                except ImportError:
                    # self._gcd_import has put an entry into self.badmodules,
                    # so continue processing
                    pass
            ## else:
            ##     self._add_badmodule('{}.{}'.format(mod.__name__, x))


    def _resolve_name(self, name, package, level):
        """Resolve a relative module name to an absolute one."""
        assert level > 0
        # This method must only be called for relative imports.
        # Probably it could return <name> when level == 0;
        # and we can save the 'if level > 0:' test in the calling code.
        bits = package.rsplit('.', level - 1)
        if len(bits) < level:
            raise ValueError('attempted relative import beyond top-level package')
        base = bits[0]
        return '{}.{}'.format(base, name) if name else base


    def _sanity_check(self, name, package, level):
        """Verify arguments are 'sane'."""
        if not isinstance(name, str):
            raise TypeError("module name must be str, not {}".format(type(name)))
        if level < 0:
            raise ValueError('level must be >= 0')
        if package:
            if not isinstance(package, str):
                raise TypeError("__package__ not set to a string")
            elif package not in self.modules:
                msg = ("Parent module {!r} not loaded, cannot perform relative "
                       "import")
                raise SystemError(msg.format(package))
        if not name and level == 0:
            raise ValueError("Empty module name")


    def _calc___package__(self, caller):
        """Calculate what __package__ should be.

        __package__ is not guaranteed to be defined or could be set to None
        to represent that its proper value is unknown.

        """
        package = caller.__package__
        if package is None:
            package = caller.__name__
            if not hasattr(caller, "__path__"):
                package = package.rpartition('.')[0]
        return package


    def _gcd_import(self, name, package=None, level=0):
        """Import and return the module based on its name, the package
        the call is being made from, and the level adjustment.

        """
        # __main__ is always the current main module; do never import that.
        if name == "__main__":
            raise ImportError()

        self._sanity_check(name, package, level)
        if level > 0:
            name = self._resolve_name(name, package, level)
        # 'name' is now the fully qualified, absolute name of the
        # module we want to import.

        caller = self.__last_caller.__name__ if self.__last_caller else "-"

        self._depgraph[name].add(caller)

        if name in self.excludes:
            raise ImportError('No module named {!r}'.format(name), name=name)

        if name in self.modules:
            return self.modules[name]
        return self._find_and_load(name)


    def _find_and_load(self, name):
        """Find and load the module.

        Inserts the module into self.modules and returns it.
        If the module is not found or could not be imported,
        it is inserted in self.badmodules.
        """
        path = self.path
        parent = name.rpartition('.')[0]
        if parent:
            if parent not in self.modules:
                self._gcd_import(parent)
            # Crazy side-effects!
            if name in self.modules:
                return self.modules[name]
            # Backwards-compatibility; be nicer to skip the dict lookup.
            parent_module = self.modules[parent]

            try:
                # try lazy imports via attribute access (six.moves
                # does this)...
                getattr(parent_module, name.rpartition('.')[2])
                module = self.modules[name]
            except (AttributeError, KeyError):
                pass
            else:
                if hasattr(module, "__code__"):
                    self._scan_code(module.__code__, module)
                return module

            try:
                path = parent_module.__path__
            except AttributeError:
                # # this fixes 'import os.path'. Does it create other problems?
                # child = name.rpartition('.')[2]
                # if child in parent_module.__globalnames__:
                #     return parent_module
                msg = ('No module named {!r}; {} is not a package').format(name, parent)
                self._add_badmodule(name)
                raise ImportError(msg, name=name)

        try:
            spec = importlib.util.find_spec(name, path)
        except ValueError as details:
            # workaround for the .pth file for namespace packages that
            # setuptools installs.  The pth file inserts a 'damaged'
            # module into sys.modules: it has no __spec__.  Reloading
            # the module helps (at least in Python3.4).
            if details.args[0] == '{}.__spec__ is None'.format(name):
                import imp
                _ = __import__(name, path)
                imp.reload(_)
                try:
                    spec = importlib.util.find_spec(name, path)
                except ValueError:
                    spec = None
            else:
                raise
        except AssertionError as details:
            # numpy/pandas and similar packages attempt to embed setuptools
            if 'distutils has already been patched by' in details.args[0]:
                spec = None
            else:
                raise

        if spec is None:
            self._add_badmodule(name)
            raise ImportError(name)
        elif name not in self.modules:
            # The parent import may have already imported this module.
            try:
                self._load_module(spec, name)
            except ImportError:
                self._add_badmodule(name)
                raise

        # Backwards-compatibility; be nicer to skip the dict lookup.
        module = self.modules[name]

        if parent:
            # Set the module as an attribute on its parent.
            parent_module = self.modules[parent]
            setattr(parent_module, name.rpartition('.')[2], module)

        # It is important that all the required __...__ attributes at
        # the module are set before the code is scanned.
        if module.__code__:
            self._scan_code(module.__code__, module)

        return module


    def _add_badmodule(self, name):
        if name not in self.ignores:
            self.badmodules.add(name)


    def _add_module(self, name, mod):
        self.modules[name] = mod


    def _load_module(self, spec, name):
        mod = Module(spec, name, self._optimize)
        self._add_module(name, mod)
        if name in self._package_paths:
            mod.__path__.extend(self._package_paths[name])


    def _scan_code(self, code, mod):
        """
        Scan the module bytecode.

        When we encounter in import statement, we simulate the import
        by calling safe_import_hook() to find the imported modules.

        We also take note of 'static' global symbols in the module and
        add them to __globalnames__.
        """

        for what, args in self._scan_opcodes(code):
            if what == "store":
                name, = args
                mod.__globalnames__.add(name)
            elif what == "import":
                level, fromlist, name = args
                self.safe_import_hook(name, mod, fromlist, level)
            else:
                # We don't expect anything else from the generator.
                raise RuntimeError(what)

        for c in code.co_consts:
            if isinstance(c, type(code)):
                self._scan_code(c, mod)


    def _scan_opcodes(self, co, unpack=struct.unpack):
        """
        Scan the code object, and yield 'interesting' opcode combinations
        """
        instructions = []
        for inst in dis.get_instructions(co):
            instructions.append(inst)
            c = inst.opcode
            if c == IMPORT_NAME:
                ind = len(instructions) - 2
                while instructions[ind].opcode == EXTENDED_ARG:
                    ind -= 1
                assert instructions[ind].opcode == LOAD_CONST
                fromlist = instructions[ind].argval
                ind -= 1
                while instructions[ind].opcode == EXTENDED_ARG:
                    ind -= 1
                assert instructions[ind].opcode == LOAD_CONST
                level = instructions[ind].argval
                name = inst.argval
                yield "import", (level, fromlist, name)
            elif c in STORE_OPS:
                yield "store", (inst.argval,)


    def ignore(self, name):
        """If the module or package with the given name is not found,
        don't record this as an error.  If is is found, however,
        include it.
        """
        self.ignores.append(name)

    def missing(self):
        """Return a set of modules that appear to be missing. Use
        any_missing_maybe() if you want to know which modules are
        certain to be missing, and which *may* be missing.

        """
        missing = set()
        for name in self.badmodules:
            package, _, symbol = name.rpartition(".")
            if not package:
                missing.add(name)
                continue
            elif package in missing:
                continue
            if symbol not in self.modules[package].__globalnames__:
                missing.add(name)
        return missing

    def missing_maybe(self):
        """Return two sets, one with modules that are certainly
        missing and one with modules that *may* be missing. The latter
        names could either be submodules *or* just global names in the
        package.

        The reason it can't always be determined is that it's impossible to
        tell which names are imported when "from module import *" is done
        with an extension module, short of actually importing it.
        """
        missing = set()
        maybe = set()
        for name in self.badmodules:
            package, _, symbol = name.rpartition(".")
            if not package:
                missing.add(name)
                continue
            elif package in missing:
                continue
            if symbol not in self.modules[package].__globalnames__:
                if "*" in self.modules[package].__globalnames__:
                    maybe.add(name)
                else:
                    missing.add(name)
        return missing, maybe


    def report_summary(self):
        """Print the count of found and missing modules.

        """
        missing, maybe = self.missing_maybe()
        print("Found %d modules, %d are missing, %d could be missing"
              % (len(self.modules), len(missing), len(maybe)))

    def report(self):
        """Print a report to stdout, listing the found modules with
        their paths, as well as modules that are missing, or seem to
        be missing. """

        self.report_modules()
        self.report_missing()


    def report_modules(self):
        """Print a report about found modules to stdout, with their
        found paths.
        """
        print()
        print("  %-35s %s" % ("Name", "File"))
        print("  %-35s %s" % ("----", "----"))
        # Print modules found
        for name in sorted(self.modules):
            m = self.modules[name]
            if m is None:
                ## print("?", end=" ")
                continue
            elif getattr(m, "__path__", None):
                print("P", end=" ")
            else:
                print("m", end=" ")
            if m.__spec__.has_location and hasattr(m, "__file__"):
                print("%-35s" % name, getattr(m, "__file__"))
            else:
                print("%-35s" % name, "(%s)" % m.__spec__.origin)
            deps = sorted(self._depgraph[name])
            text = "\n".join(textwrap.wrap(", ".join(deps)))
            print("   imported from:\n%s" % textwrap.indent(text, "      "))


    def report_missing(self):
        """Print a report to stdout, listing those modules that are
        missing.

        """
        missing, maybe = self.missing_maybe()
        print()
        print("  %-35s" % ("%d missing Modules" % len(missing)))
        print("  %-35s" % "------------------")
        for name in sorted(missing):
            deps = sorted(self._depgraph[name])
            print("? %-35s imported from %s" % (name, ", ".join(deps)))

        # Print modules that may be missing, but then again, maybe not...
        if maybe:
            print()
            print("  %-35s" %
                  ("%d submodules that appear to be missing, but"
                   " could also be global names"
                   " in the parent package" % len(maybe)))
            print("  %-35s" %
                  "-----------------------------------------"
                  "----------------------------------------------------")
            for name in sorted(maybe):
                deps = sorted(self._depgraph[name])
                print("? %-35s imported from %s" % (name, ", ".join(deps)))


################################################################


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

    def __init__(self, spec, name, optimize):
        self.__optimize__ = optimize
        self.__globalnames__ = set()

        self.__name__ = name
        self.__spec__ = spec
        self.__code_object__ = None

        try:
            loader = self.__loader__ = spec.loader
        except AttributeError:
            loader = self.__loader__ = None

        if hasattr(loader, "get_filename"):
            # python modules
            fnm = loader.get_filename(name)
            self.__file__ = fnm
            if loader.is_package(name):
                self.__path__ = [os.path.dirname(fnm)]
        elif hasattr(loader, "path"):
            # extension modules
            fnm = loader.path
            self.__file__ = fnm
            if loader.is_package(name):
                self.__path__ = [os.path.dirname(fnm)]
        elif loader is None and hasattr(spec, "submodule_search_locations"):
            # namespace modules have no loader
            self.__path__ = spec.submodule_search_locations
        elif hasattr(loader, "is_package"):
            # frozen or builtin modules
            if loader.is_package(name):
                self.__path__ = [name]

        if getattr(self, '__package__', None) is None:
            try:
                self.__package__ = self.__name__
                if not hasattr(self, '__path__'):
                    self.__package__ = self.__package__.rpartition('.')[0]
            except AttributeError:
                pass

    @property
    def __dest_file__(self):
        """Gets the destination path for the module that will be used at compilation time."""
        if self.__optimize__:
            bytecode_suffix = OPTIMIZED_BYTECODE_SUFFIXES[0]
        else:
            bytecode_suffix = DEBUG_BYTECODE_SUFFIXES[0]
        if hasattr(self, "__path__"):
            return self.__name__.replace(".", "\\") + "\\__init__" + bytecode_suffix
        else:
            return self.__name__.replace(".", "\\") + bytecode_suffix


    @property
    def __code__(self):
        if self.__code_object__ is None:
            if self.__loader__ is None: # implicit namespace packages
                return None
            if self.__loader__.__class__ == importlib.machinery.ExtensionFileLoader:
                return None
            if 'VendorImporter' in str(self.__loader__.__class__):
                return None
            try:
                try:
                    source = self.__source__
                except Exception:
                    import traceback; traceback.print_exc()
                    raise RuntimeError("loading %r" % self) from None
                if source is not None:
                    __file__ = self.__dest_file__ \
                               if hasattr(self, "__file__") else "<string>"
                    try:
                        self.__code_object__ = compile(source, __file__, "exec",
                                                       optimize=self.__optimize__)
                    except Exception:
                        import traceback; traceback.print_exc()
                        raise RuntimeError("compiling %r" % self) from None
                elif hasattr(self, "__file__") and not self.__file__.endswith(".pyd"):
                    # XXX Remove the following line if the Bug is never triggered!
                    raise RuntimeError("should read __file__ to get the source???")
            except RuntimeError:
                if self.__optimize__ != sys.flags.optimize:
                    raise
                print("Falling back to loader to get code for module %s" % self.__name__)
                self.__code_object__ = self.__loader__.get_code(self.__name__)
        return self.__code_object__


    @property
    def __source__(self):
        return self.__loader__.get_source(self.__name__)


    def __repr__(self):
        s = "Module(%s" % self.__name__
        if getattr(self, "__file__", None) is not None:
            s = s + ", %r" % (self.__file__,)
        if getattr(self, "__path__", None) is not None:
            s = s + ", %r" % (self.__path__,)
        return s + ")"


################################################################


def usage(script):
    import textwrap
    helptext = """\
    Usage: {0} [options] [scripts]

    ModuleFinder scans the bytecode of Python scripts and modules for
    import statements, and collects the modules that are needed to run
    this code.

    Options:

        -h
        --help
            Print this help

    What to scan:

        -i <modname>
        --import <modname>
            Import a module

        -p <packagename>
        --package <packagename>
            Import a complete package with all its modules

        -x <modname>
        --exclude <modname>
            Exclude a module

    How to scan:

        -O
        --optimize
            Use the optimized bytecode

        -v
        --verbose
            Print reconstructed import statements that are found while
            scanning the byte code.

    Reporting:

        -f <modname>
        --from <modname>
            Print a listing of modules that import modname

        -r
        --report
            Print a detailed eport listing all the found modules, the
            missing modules, and which module imported them.

        -s
        --summary
            Print a single line listing how many modules were found
            and how many modules are missing

        -m
        --missing
            Print detailed report about missing modules

    """

    text = textwrap.dedent(helptext.format(os.path.basename(script)))
    print(text)

def main():
    import getopt
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],
                                       "x:f:hi:Op:rsvm",
                                       ["exclude=",
                                        "from=",
                                        "help",
                                        "import=",
                                        "optimize",
                                        "package",
                                        "report",
                                        "summary",
                                        "verbose",
                                        "missing",
                                        ])
    except getopt.GetoptError as err:
        print("Error: %s." % err)
        sys.exit(2)

    verbose = 0
    excludes = []
    report = 0
    modules = []
    show_from = []
    optimize = 0
    summary = 0
    packages = []
    missing = 0
    for o, a in opts:
        if o in ("-h", "--help"):
            usage(sys.argv[0])
            return 0
        if o in ("-x", "--excludes"):
            excludes.append(a)
        elif o in ("-i", "--import"):
            modules.append(a)
        elif o in ("-f", "--from"):
            show_from.append(a)
        elif o in ("-v", "--verbose"):
            verbose += 1
        elif o in ("-r", "--report"):
            report += 1
        elif o in ("-O", "--optimize"):
            optimize += 1
        elif o in ("-s", "--summary"):
            summary = 1
        elif o in ("-p", "--package"):
            packages.append(a)
        elif o in ("-m", "--missing"):
            missing = 1

    mf = ModuleFinder(
        excludes=excludes,
        verbose=verbose,
        optimize=optimize,
        )
    for name in modules:
        # Hm, call import_hook() or safe_import_hook() here?
        if name.endswith(".*"):
            mf.import_hook(name[:-2], None, ["*"])
        else:
            mf.import_hook(name)
    for name in packages:
        mf.import_package(name)
    for path in args:
        mf.run_script(path)
    if report:
        mf.report()
    if missing:
        mf.report_missing()
    if summary:
        mf.report_summary()
    for modname in show_from:
        print(modname, "imported from:")
        for x in sorted(mf._depgraph[modname]):
            print("   ", x)


if __name__ == "__main__":
    main()

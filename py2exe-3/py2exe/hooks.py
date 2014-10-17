# -*- coding: utf-8 -*-
#
# Hooks module for py2exe.
# Inspired by cx_freeze's hooks.py, which is:
#
#    Copyright © 2007-2013, Anthony Tuininga.
#    Copyright © 2001-2006, Computronix (Canada) Ltd., Edmonton, Alberta, Canada.
#    All rights reserved.
#
import os, sys

# Exclude modules that the standard library imports (conditionally),
# but which are not present on windows.
#
# _memimporter can be excluded because it is built into the run-stub.
windows_excludes = """
_curses
_dummy_threading
_emx_link
_gestalt
_posixsubprocess
ce
clr
console
fcntl
grp
java
org
os2
posix
pwd
site
termios
vms_lib
_memimporter
""".split()

def init_finder(finder):
    # what about renamed functions, like urllib.pathname2url?
    #
    # We should use ignore() for Python 2 names so that my py2to3
    # importhook works.  For modules that are not present on Windows,
    # we should probably use excludes.append()
    finder.excludes.extend(windows_excludes)

    # python2 modules are ignored (but not excluded)
    finder.ignore("BaseHTTPServer")
    finder.ignore("ConfigParser")
    finder.ignore("IronPython")
    finder.ignore("SimpleHTTPServer")
    finder.ignore("StringIO")
    finder.ignore("__builtin__")
    finder.ignore("_winreg")
    finder.ignore("cPickle")
    finder.ignore("cStringIO")
    finder.ignore("commands")
    finder.ignore("compiler")
    finder.ignore("copy_reg")
    finder.ignore("dummy_thread")
    finder.ignore("future_builtins")
    finder.ignore("htmlentitydefs")
    finder.ignore("httplib")
    finder.ignore("md5")
    finder.ignore("new")
    finder.ignore("thread")
    finder.ignore("unittest2")
    finder.ignore("urllib2")
    finder.ignore("urlparse")

def hook_pycparser(finder, module):
    """pycparser needs lextab.py and yacctab.py which are not picked
    up automatically.  Make sure the complete package is included;
    otherwise the exe-files may create yacctab.py and lextab.py when
    they are run.
    """
    finder.import_package_later("pycparser")

def hook_pycparser__build_tables(finder, module):
    finder.ignore("lextab")
    finder.ignore("yacctab")
    finder.ignore("_ast_gen")
    finder.ignore("c_ast")

def hook_pycparser_ply(finder, module):
    finder.ignore("lex")
    finder.ignore("ply")

def hook_OpenSSL(finder, module):
    """OpenSSL needs the cryptography package."""
    finder.import_package_later("cryptography")

def hook_cffi_cparser(finder, module):
    finder.ignore("cffi._pycparser")

def hook_cffi(finder, module):
    # We need to patch two methods in the
    # cffi.vengine_cpy.VCPythonEngine class so that cffi libraries
    # work from within zip-files.
    finder.add_bootcode("""
def patch_cffi():
    def find_module(self, module_name, path, so_suffixes):
        import sys
        name = "%s.%s" % (self.verifier.ext_package, module_name)
        try:
            __import__(name)
        except ImportError:
            return None
        self.__module = mod = sys.modules[name]
        return mod.__file__

    def load_library(self):
        from cffi import ffiplatform
        import sys
        # XXX review all usages of 'self' here!
        # import it as a new extension module
        module = self.__module
        #
        # call loading_cpy_struct() to get the struct layout inferred by
        # the C compiler
        self._load(module, 'loading')
        #
        # the C code will need the <ctype> objects.  Collect them in
        # order in a list.
        revmapping = dict([(value, key)
                           for (key, value) in self._typesdict.items()])
        lst = [revmapping[i] for i in range(len(revmapping))]
        lst = list(map(self.ffi._get_cached_btype, lst))
        #
        # build the FFILibrary class and instance and call _cffi_setup().
        # this will set up some fields like '_cffi_types', and only then
        # it will invoke the chained list of functions that will really
        # build (notably) the constant objects, as <cdata> if they are
        # pointers, and store them as attributes on the 'library' object.
        class FFILibrary(object):
            _cffi_python_module = module
            _cffi_ffi = self.ffi
            _cffi_dir = []
            def __dir__(self):
                return FFILibrary._cffi_dir + list(self.__dict__)
        library = FFILibrary()
        if module._cffi_setup(lst, ffiplatform.VerificationError, library):
            import warnings
            warnings.warn("reimporting %r might overwrite older definitions"
                          % (self.verifier.get_module_name()))
        #
        # finally, call the loaded_cpy_xxx() functions.  This will perform
        # the final adjustments, like copying the Python->C wrapper
        # functions from the module to the 'library' object, and setting
        # up the FFILibrary class with properties for the global C variables.
        self._load(module, 'loaded', library=library)
        module._cffi_original_ffi = self.ffi
        module._cffi_types_of_builtin_funcs = self._types_of_builtin_functions
        return library


    from cffi.vengine_cpy import VCPythonEngine

    VCPythonEngine.find_module = find_module
    VCPythonEngine.load_library = load_library

patch_cffi()
del patch_cffi
""")
    

def hook_multiprocessing(finder, module):
    module.__globalnames__.add("AuthenticationError")
    module.__globalnames__.add("BufferTooShort")
    module.__globalnames__.add("Manager")
    module.__globalnames__.add("TimeoutError")
    module.__globalnames__.add("cpu_count")
    module.__globalnames__.add("current_process")
    module.__globalnames__.add("get_context")
    module.__globalnames__.add("get_start_method")
    module.__globalnames__.add("set_start_method")

    module.__globalnames__.add("JoinableQueue")
    module.__globalnames__.add("Lock")
    module.__globalnames__.add("Process")
    module.__globalnames__.add("Queue")
    module.__globalnames__.add("freeze_support")

def import_psutil(finder, module):
    """Exclude stuff for other operating systems."""
    finder.excludes.append("_psutil_bsd")
    finder.excludes.append("_psutil_linux")
    finder.excludes.append("_psutil_osx")
    finder.excludes.append("_psutil_posix")
    finder.excludes.append("_psutil_sunos")

def hook_PIL(finder, module):
    # c:\Python33-64\lib\site-packages\PIL
    """Pillow loads plugins"""
    # Exclude python 2 imports
    finder.excludes.append("Tkinter")
    finder.import_package_later("PIL")

def hook__socket(finder, module):
    """
    _socket.pyd uses the 'idna' encoding; and that requires
    'unicodedata.pyd'.
    """
    finder.import_hook("encodings.idna")
    finder.import_hook("unicodedata")

def hook_pyreadline(finder, module):
    """
    """
    finder.ignore("IronPythonConsole")
    finder.excludes.append("StringIO") # in pyreadline.py3k_compat
    finder.ignore("System")
    finder.excludes.append("sets")
    finder.ignore("startup")

def hook_xml_etree_ElementTree(finder, module):
    """ElementC14N is an optional extension. Ignore if it is not
    found.
    """
    finder.ignore("ElementC14N")

def hook_urllib_request(finder, module):
    """urllib.request imports _scproxy on darwin
    """
    finder.excludes.append("_scproxy")

def hook_pythoncom(finder, module):
    """pythoncom is a Python extension module with .dll extension,
    usually in the windows system directory as pythoncom3X.dll.
    """
    import pythoncom
    finder.add_dll(pythoncom.__file__)

def hook_pywintypes(finder, module):
    """pywintypes is a Python extension module with .dll extension,
    usually in the windows system directory as pywintypes3X.dll.
    """
    import pywintypes
    finder.add_dll(pywintypes.__file__)

def hook_win32com(finder, module):
    """The win32com package extends it's __path__ at runtime.
    """
    finder.import_hook("pywintypes")
    finder.import_hook("pythoncom")
    import win32com
    module.__path__ = win32com.__path__

def hook_win32api(finder, module):
    """win32api.FindFiles(...) needs this."""
    finder.import_hook("pywintypes")
    finder.import_hook("win32timezone")

def hook_tkinter(finder, module):
    """Recusively copy tcl and tk directories.
    """
    # It probably doesn't make sense to exclude tix from the tcl distribution,
    # and only copy it when tkinter.tix is imported...
    import tkinter._fix as fix
    tcl_dir = os.path.normpath(os.path.join(fix.tcldir, ".."))
    assert os.path.isdir(tcl_dir)
    finder.add_datadirectory("tcl", tcl_dir, recursive=True)
    finder.set_min_bundle("tkinter", 2)

def hook_six(finder, module):
    """six.py has an object 'moves'. This allows to import
    modules/packages via attribute access under new names.

    We install a fake module named 'six.moves' which simulates this
    behaviour.
    """

    class SixImporter(type(module)):
        """Simulate six.moves.

        Import renamed modules when retrived as attributes.
        """

        __code__ = None

        def __init__(self, mf, *args, **kw):
            import six
            self.__moved_modules = {item.name: item.mod
                                    for item in six._moved_attributes
                                    if isinstance(item, six.MovedModule)}
            super().__init__(*args, **kw)
            self.__finder = mf

        def __getattr__(self, name):
            if name in self.__moved_modules:
                renamed = self.__moved_modules[name]
                self.__finder.safe_import_hook(renamed, caller=self)
                mod = self.__finder.modules[renamed]
                # add the module again with the renamed name:
                self.__finder._add_module("six.moves." + name, mod)
                return mod
            else:
                raise AttributeError(name)

    m = SixImporter(finder,
                    None, "six.moves", finder._optimize)
    finder._add_module("six.moves", m)
    


def hook_matplotlib(finder, module):
    """matplotlib requires data files in a 'mpl-data' subdirectory in
    the same directory as the executable.
    """
    # c:\Python33\lib\site-packages\matplotlib
    mpl_data_path = os.path.join(os.path.dirname(module.__loader__.path),
                                 "mpl-data")
    finder.add_datadirectory("mpl-data", mpl_data_path, recursive=True)
    finder.excludes.append("wx")
    # XXX matplotlib requires tkinter which modulefinder does not
    # detect because of the six bug.

def hook_numpy(finder, module):
    """numpy for Python 3 still tries to import some Python 2 modules;
    exclude them."""
    # I'm not sure if we can safely exclude these:
    finder.ignore("Numeric")
    finder.ignore("numarray")
    finder.ignore("numpy_distutils")
    finder.ignore("setuptools")
    finder.ignore("Pyrex")
    finder.ignore("nose")
    finder.ignore("scipy")

def hook_nose(finder, module):
    finder.ignore("IronPython")
    finder.ignore("cStringIO")
    finder.ignore("unittest2")

def hook_sysconfig(finder, module):
    finder.ignore("_sysconfigdata")

def hook_numpy_random_mtrand(finder, module):
    """the numpy.random.mtrand module is an extension module and the
    numpy.random module imports * from this module; define the list of
    global names available to this module in order to avoid spurious
    errors about missing modules.
    """
    module.__globalnames__.add('RandomState')
    module.__globalnames__.add('beta')
    module.__globalnames__.add('binomial')
    module.__globalnames__.add('bytes')
    module.__globalnames__.add('chisquare')
    module.__globalnames__.add('choice')
    module.__globalnames__.add('dirichlet')
    module.__globalnames__.add('exponential')
    module.__globalnames__.add('f')
    module.__globalnames__.add('gamma')
    module.__globalnames__.add('geometric')
    module.__globalnames__.add('get_state')
    module.__globalnames__.add('gumbel')
    module.__globalnames__.add('hypergeometric')
    module.__globalnames__.add('laplace')
    module.__globalnames__.add('logistic')
    module.__globalnames__.add('lognormal')
    module.__globalnames__.add('logseries')
    module.__globalnames__.add('multinomial')
    module.__globalnames__.add('multivariate_normal')
    module.__globalnames__.add('negative_binomial')
    module.__globalnames__.add('noncentral_chisquare')
    module.__globalnames__.add('noncentral_f')
    module.__globalnames__.add('normal')
    module.__globalnames__.add('np')
    module.__globalnames__.add('operator')
    module.__globalnames__.add('pareto')
    module.__globalnames__.add('permutation')
    module.__globalnames__.add('poisson')
    module.__globalnames__.add('power')
    module.__globalnames__.add('rand')
    module.__globalnames__.add('randint')
    module.__globalnames__.add('randn')
    module.__globalnames__.add('random_integers')
    module.__globalnames__.add('random_sample')
    module.__globalnames__.add('rayleigh')
    module.__globalnames__.add('seed')
    module.__globalnames__.add('set_state')
    module.__globalnames__.add('shuffle')
    module.__globalnames__.add('standard_cauchy')
    module.__globalnames__.add('standard_exponential')
    module.__globalnames__.add('standard_gamma')
    module.__globalnames__.add('standard_normal')
    module.__globalnames__.add('standard_t')
    module.__globalnames__.add('triangular')
    module.__globalnames__.add('uniform')
    module.__globalnames__.add('vonmises')
    module.__globalnames__.add('wald')
    module.__globalnames__.add('weibull')
    module.__globalnames__.add('zipf')

def hook_numpy_distutils(finder, module):
    """In a 'if sys.version_info[0] < 3:' block numpy.distutils does
    an implicit relative import: 'import __config__'.  This will not
    work in Python3 so ignore it.
    """
    finder.excludes.append("__config__")

def hook_numpy_f2py(finder, module):
    """ numpy.f2py tries to import __svn_version__.  Ignore when his fails.
    """
    finder.excludes.append("__svn_version__")

def hook_numpy_core_umath(finder, module):
    """the numpy.core.umath module is an extension module and the numpy module
       imports * from this module; define the list of global names available
       to this module in order to avoid spurious errors about missing
       modules"""
    module.__globalnames__.add("add")
    module.__globalnames__.add("absolute")
    module.__globalnames__.add("arccos")
    module.__globalnames__.add("arccosh")
    module.__globalnames__.add("arcsin")
    module.__globalnames__.add("arcsinh")
    module.__globalnames__.add("arctan")
    module.__globalnames__.add("arctanh")
    module.__globalnames__.add("bitwise_and")
    module.__globalnames__.add("bitwise_or")
    module.__globalnames__.add("bitwise_xor")
    module.__globalnames__.add("ceil")
    module.__globalnames__.add("conjugate")
    module.__globalnames__.add("cosh")
    module.__globalnames__.add("divide")
    module.__globalnames__.add("exp")
    module.__globalnames__.add("e")
    module.__globalnames__.add("fabs")
    module.__globalnames__.add("floor")
    module.__globalnames__.add("floor_divide")
    module.__globalnames__.add("fmod")
    module.__globalnames__.add("geterrobj")
    module.__globalnames__.add("greater")
    module.__globalnames__.add("hypot")
    module.__globalnames__.add("invert")
    module.__globalnames__.add("isfinite")
    module.__globalnames__.add("isinf")
    module.__globalnames__.add("isnan")
    module.__globalnames__.add("less")
    module.__globalnames__.add("left_shift")
    module.__globalnames__.add("log")
    module.__globalnames__.add("logical_and")
    module.__globalnames__.add("logical_not")
    module.__globalnames__.add("logical_or")
    module.__globalnames__.add("logical_xor")
    module.__globalnames__.add("maximum")
    module.__globalnames__.add("minimum")
    module.__globalnames__.add("multiply")
    module.__globalnames__.add("negative")
    module.__globalnames__.add("not_equal")
    module.__globalnames__.add("power")
    module.__globalnames__.add("remainder")
    module.__globalnames__.add("right_shift")
    module.__globalnames__.add("sign")
    module.__globalnames__.add("signbit")
    module.__globalnames__.add("sinh")
    module.__globalnames__.add("sqrt")
    module.__globalnames__.add("tan")
    module.__globalnames__.add("tanh")
    module.__globalnames__.add("true_divide")

def hook_numpy_core_numerictypes(finder, module):
    """the numpy.core.numerictypes module adds a number of items to itself
       dynamically; define these to avoid spurious errors about missing
       modules"""
    module.__globalnames__.add("bool_")
    module.__globalnames__.add("cdouble")
    module.__globalnames__.add("complexfloating")
    module.__globalnames__.add("csingle")
    module.__globalnames__.add("double")
    module.__globalnames__.add("longdouble")
    module.__globalnames__.add("float32")
    module.__globalnames__.add("float64")
    module.__globalnames__.add("float_")
    module.__globalnames__.add("inexact")
    module.__globalnames__.add("integer")
    module.__globalnames__.add("intc")
    module.__globalnames__.add("int32")
    module.__globalnames__.add("number")
    module.__globalnames__.add("single")

def hook_numpy_core(finder, module):
    finder.ignore("numpy.core._dotblas")

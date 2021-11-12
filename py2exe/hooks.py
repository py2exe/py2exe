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

def hook_certifi(finder, module):
    import certifi
    finder.add_libfile("cacert.pem", certifi.where())
    finder.add_bootcode("""
def patch_certifi():
    import certifi

    def override_where():
        # change this to match the location of cacert.pem
        import os.path
        pt = os.path.dirname(certifi.__file__)
        while not os.path.exists(pt):
            pt = os.path.dirname(pt)
        pt = os.path.dirname(pt)
        return os.path.join(pt, 'cacert.pem')

    certifi.where = override_where
    certifi.core.where = override_where

patch_certifi()
del patch_certifi
""")

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
    module.globalnames["AuthenticationError"] = 1
    module.globalnames["BufferTooShort"] = 1
    module.globalnames["Manager"] = 1
    module.globalnames["TimeoutError"] = 1
    module.globalnames["cpu_count"] = 1
    module.globalnames["current_process"] = 1
    module.globalnames["get_context"] = 1
    module.globalnames["get_start_method"] = 1
    module.globalnames["set_start_method"] = 1

    module.globalnames["JoinableQueue"] = 1
    module.globalnames["Lock"] = 1
    module.globalnames["Process"] = 1
    module.globalnames["Queue"] = 1
    module.globalnames["freeze_support"] = 1

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
    Also 'imp' is required from Python 3.6
    """
    finder.import_hook("encodings.idna")
    finder.import_hook("unicodedata")
    if sys.version_info >= (3,6,0):
        finder.import_hook("imp")

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

def hook_urllib3(finder, module):
    """urllib3 embeds a copy of six that requires queue.
    """
    finder.import_hook("queue")

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
    """Recusively copy tcl and tk directories"""
    from tkinter import Tcl
    from _tkinter import TK_VERSION
    tcl_dir = os.path.normpath(Tcl().eval("info library"))
    assert os.path.isdir(tcl_dir)
    finder.add_datadirectory("lib/tcl", tcl_dir, recursive=True)
    tk_dir = os.path.join(os.path.dirname(tcl_dir), 'tk{}'.format(TK_VERSION))
    assert os.path.isdir(tk_dir)
    finder.add_datadirectory("lib/tk", tk_dir, recursive=True)
    if sys.version_info >= (3,6,0):
        finder.import_hook("imp")

    # add environment variables that point to the copied paths at runtime
    finder.add_bootcode("""
def tk_env_paths():
    import os
    import sys
    import _tkinter
    basepath = os.path.dirname(sys.executable)
    tcl_dir = os.path.join(basepath, 'lib', 'tcl')
    tk_dir = os.path.join(basepath, 'lib', 'tk')
    os.environ["TCL_LIBRARY"] = tcl_dir
    os.environ["TK_LIBRARY"] = tk_dir

tk_env_paths()
del tk_env_paths
""")

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
            self.__moved_modules.pop('urllib')
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
                    "six.moves", None, finder._optimize)
    finder._add_module("six.moves", m)

def hook_infi(finder, module):
    """Thw whole infi namespace package relies on pkg_resources for
    loading modules and data files.
    """
    finder.import_hook("pkg_resources")

def hook_matplotlib(finder, module):
    """matplotlib requires data files in a 'mpl-data' subdirectory in
    the same directory as the executable.
    """
    import ast
    from pkg_resources._vendor.packaging import version as pkgversion

    import matplotlib

    mpl_data_path = matplotlib.get_data_path()
    finder.add_datadirectory("mpl-data", mpl_data_path, recursive=True)

    finder.excludes.append("wx")
    # XXX matplotlib requires tkinter which modulefinder does not
    # detect because of the six bug.

    # matplotlib requires a patch in its __init__ to correctly locate the `mpi-data` folder from where we put it
    # see issue #71 fof further details
    tree = ast.parse(module.__source__)

    # matplotlib <=3.3.4 requires '_get_data_path' to be patched
    # matplotlib >= 3.4.0 requires 'get_data_path' to be patched
    mpl_version = pkgversion.parse(matplotlib.__version__)
    node_to_be_patched = 'get_data_path' if mpl_version >= pkgversion.parse('3.4.0') else '_get_data_path'

    class ChangeDef(ast.NodeTransformer):
        def visit_FunctionDef(self, node: ast.FunctionDef):
            if node.name == node_to_be_patched:
                node.body = ast.parse('return os.path.join(os.path.dirname(sys.executable), "mpl-data")').body
            return node

    t = ChangeDef()
    patched_tree = t.visit(tree)

    module.__code_object__ = compile(patched_tree, module.__file__, "exec", optimize=module.__optimize__)

    finder.import_hook("mpl_toolkits")

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
    #add numpy external DLLs to the bundle
    numpy_libs_path = os.path.join(os.path.dirname(module.__loader__.path), '.libs')
    if os.path.isdir(numpy_libs_path):
        from os import listdir
        dlls = [os.path.join(numpy_libs_path, fln)
                for fln in listdir(numpy_libs_path)
                if fln.endswith('.dll')]
        for dll in dlls:
            finder.add_dll(dll)

def hook_nose(finder, module):
    finder.ignore("IronPython")
    finder.ignore("cStringIO")
    finder.ignore("unittest2")

def hook_sysconfig(finder, module):
    finder.ignore("_sysconfigdata")

def hook_numpy_random(finder, module):
    finder.ignore("_examples")
    finder.ignore("tests")

def hook_numpy_random_mtrand(finder, module):
    """the numpy.random.mtrand module is an extension module and the
    numpy.random module imports * from this module; define the list of
    global names available to this module in order to avoid spurious
    errors about missing modules.
    """
    module.globalnames['RandomState'] = 1
    module.globalnames['beta'] = 1
    module.globalnames['binomial'] = 1
    module.globalnames['bytes'] = 1
    module.globalnames['chisquare'] = 1
    module.globalnames['choice'] = 1
    module.globalnames['dirichlet'] = 1
    module.globalnames['exponential'] = 1
    module.globalnames['f'] = 1
    module.globalnames['gamma'] = 1
    module.globalnames['geometric'] = 1
    module.globalnames['get_state'] = 1
    module.globalnames['gumbel'] = 1
    module.globalnames['hypergeometric'] = 1
    module.globalnames['laplace'] = 1
    module.globalnames['logistic'] = 1
    module.globalnames['lognormal'] = 1
    module.globalnames['logseries'] = 1
    module.globalnames['multinomial'] = 1
    module.globalnames['multivariate_normal'] = 1
    module.globalnames['negative_binomial'] = 1
    module.globalnames['noncentral_chisquare'] = 1
    module.globalnames['noncentral_f'] = 1
    module.globalnames['normal'] = 1
    module.globalnames['np'] = 1
    module.globalnames['operator'] = 1
    module.globalnames['pareto'] = 1
    module.globalnames['permutation'] = 1
    module.globalnames['poisson'] = 1
    module.globalnames['power'] = 1
    module.globalnames['rand'] = 1
    module.globalnames['randint'] = 1
    module.globalnames['randn'] = 1
    module.globalnames['random_integers'] = 1
    module.globalnames['random_sample'] = 1
    module.globalnames['rayleigh'] = 1
    module.globalnames['seed'] = 1
    module.globalnames['set_state'] = 1
    module.globalnames['shuffle'] = 1
    module.globalnames['standard_cauchy'] = 1
    module.globalnames['standard_exponential'] = 1
    module.globalnames['standard_gamma'] = 1
    module.globalnames['standard_normal'] = 1
    module.globalnames['standard_t'] = 1
    module.globalnames['triangular'] = 1
    module.globalnames['uniform'] = 1
    module.globalnames['vonmises'] = 1
    module.globalnames['wald'] = 1
    module.globalnames['weibull'] = 1
    module.globalnames['zipf'] = 1

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
    module.globalnames["add"] = 1
    module.globalnames["absolute"] = 1
    module.globalnames["arccos"] = 1
    module.globalnames["arccosh"] = 1
    module.globalnames["arcsin"] = 1
    module.globalnames["arcsinh"] = 1
    module.globalnames["arctan"] = 1
    module.globalnames["arctanh"] = 1
    module.globalnames["bitwise_and"] = 1
    module.globalnames["bitwise_or"] = 1
    module.globalnames["bitwise_xor"] = 1
    module.globalnames["ceil"] = 1
    module.globalnames["conjugate"] = 1
    module.globalnames["cosh"] = 1
    module.globalnames["divide"] = 1
    module.globalnames["exp"] = 1
    module.globalnames["e"] = 1
    module.globalnames["fabs"] = 1
    module.globalnames["floor"] = 1
    module.globalnames["floor_divide"] = 1
    module.globalnames["fmod"] = 1
    module.globalnames["geterrobj"] = 1
    module.globalnames["greater"] = 1
    module.globalnames["hypot"] = 1
    module.globalnames["invert"] = 1
    module.globalnames["isfinite"] = 1
    module.globalnames["isinf"] = 1
    module.globalnames["isnan"] = 1
    module.globalnames["less"] = 1
    module.globalnames["left_shift"] = 1
    module.globalnames["log"] = 1
    module.globalnames["logical_and"] = 1
    module.globalnames["logical_not"] = 1
    module.globalnames["logical_or"] = 1
    module.globalnames["logical_xor"] = 1
    module.globalnames["maximum"] = 1
    module.globalnames["minimum"] = 1
    module.globalnames["multiarray"] = 1
    module.globalnames["multiply"] = 1
    module.globalnames["negative"] = 1
    module.globalnames["not_equal"] = 1
    module.globalnames["power"] = 1
    module.globalnames["remainder"] = 1
    module.globalnames["right_shift"] = 1
    module.globalnames["sign"] = 1
    module.globalnames["signbit"] = 1
    module.globalnames["sinh"] = 1
    module.globalnames["sqrt"] = 1
    module.globalnames["tan"] = 1
    module.globalnames["tanh"] = 1
    module.globalnames["true_divide"] = 1

def hook_numpy_core_numerictypes(finder, module):
    """the numpy.core.numerictypes module adds a number of items to itself
       dynamically; define these to avoid spurious errors about missing
       modules"""
    module.globalnames["bool_"] = 1
    module.globalnames["cdouble"] = 1
    module.globalnames["complexfloating"] = 1
    module.globalnames["csingle"] = 1
    module.globalnames["double"] = 1
    module.globalnames["longdouble"] = 1
    module.globalnames["float32"] = 1
    module.globalnames["float64"] = 1
    module.globalnames["float_"] = 1
    module.globalnames["inexact"] = 1
    module.globalnames["integer"] = 1
    module.globalnames["intc"] = 1
    module.globalnames["int32"] = 1
    module.globalnames["number"] = 1
    module.globalnames["single"] = 1

def hook_numpy_core(finder, module):
    finder.ignore("numpy.core._dotblas")
    numpy_core_path = os.path.dirname(module.__loader__.path)
    #add mkl dlls from numpy.core, if present
    from os import listdir
    dlls = [os.path.join(numpy_core_path,mkl)
            for mkl in listdir(numpy_core_path)
            if mkl.startswith('mkl_') or mkl in ['libmmd.dll', 'libifcoremd.dll', 'libiomp5md.dll']]
    for dll in dlls:
        finder.add_dll(dll)

def hook_pandas(finder, module):
    #pd_lib_path = os.path.join(os.path.dirname(module.__loader__.path), "_libs")
    #finder.add_datadirectory("mpl-data", mpl_data_path, recursive=True)
    depth = getattr(finder,"recursion_depth_pandas", 0)
    if depth==0:
        finder.recursion_depth_pandas = depth + 1
        finder.import_hook("pandas._libs.tslibs.base")
        finder.recursion_depth_pandas = depth

def hook_pkg_resources(finder, module):
    depth = getattr(finder,"recursion_depth_pkg_resources", 0)
    if depth==0:
        finder.recursion_depth_pkg_resources = depth + 1
        finder.import_package("pkg_resources._vendor")
        finder.import_package("pkg_resources._vendor.packaging")
        finder.recursion_depth_pkg_resources = depth

def hook_Cryptodome(finder, module):
    """pycryptodomex distributes the same package as pycryptodome under a different package name"""
    hook_Crypto(finder, module)

def hook_Crypto(finder, module):
    """pycryptodome includes compiled libraries as if they were Python C extensions (as .pyd files).
    However, they are not, as they cannot be imported by Python. Hence, those files should be treated
    as .dll files. Furthermore, pycryptodome needs to be patched to import those libraries from an external
    path, as their import mechanism will not work from the zip file nor from the executable."""
    # copy all the "pyd" files from pycryptodome to the bundle directory with the correct folder structure
    crypto_path = os.path.dirname(module.__loader__.path)
    from pathlib import Path
    for path in Path(crypto_path).rglob('*.pyd'):
        finder.add_libfile(str(path.relative_to(os.path.dirname(crypto_path))), path)

    package_name = module.__name__

    # patch pycryptodome to look for its "pyd" files in the bundle directory
    finder.add_bootcode(f"""
def patch_Crypto():
    import os
    import sys

    try:
        import {package_name}.Util._file_system
    except ImportError:
        # the hook should not work for pycrypto
        return

    def override_filename(dir_comps, filename):
        if dir_comps[0] != "{package_name}":
            raise ValueError("Only available for modules under '{package_name}'")

        dir_comps = list(dir_comps[1:]) + [filename]
        root_lib = os.path.join(os.path.dirname(sys.executable), '{package_name}')

        return os.path.join(root_lib, *dir_comps)

    {package_name}.Util._file_system.pycryptodome_filename = override_filename

patch_Crypto()
del patch_Crypto
""")

def hook_scipy(finder, module):
    #add numpy external DLLs to the bundle
    depth = getattr(finder,"recursion_depth_scipy",0)
    if depth==0:
        finder.recursion_depth_scipy = depth + 1
        finder.import_package("scipy._lib")
        finder.import_package("scipy.spatial.transform")
        finder.recursion_depth_scipy = depth
    scipy_libs_path = os.path.join(os.path.dirname(module.__loader__.path), '.libs')
    if os.path.isdir(scipy_libs_path):
        from os import listdir
        dlls = [os.path.join(scipy_libs_path, fln)
                for fln in listdir(scipy_libs_path)
                if fln.endswith('.dll')]
        for dll in dlls:
            finder.add_dll(dll)

def hook_scipy_special(finder, module):
    #import pdb;pdb.set_trace()
    depth = getattr(finder,"recursion_depth_special",0)
    if depth==0:
        finder.recursion_depth_special = depth + 1
        finder.import_hook("scipy.special._ufuncs_cxx")
        finder.import_hook("scipy.special.orthogonal")
        finder.import_hook("scipy", fromlist=("linalg",))
        finder.recursion_depth_special = depth

def hook_scipy_linalg(finder, module):
    depth = getattr(finder,"recursion_depth_linalg",0)
    if depth==0:
        finder.recursion_depth_linalg = depth + 1
        finder.import_hook("scipy.linalg.cython_blas")
        finder.import_hook("scipy.linalg.cython_lapack")
        finder.import_hook("scipy.integrate")
        finder.import_hook("scipy")
        finder.recursion_depth_linalg = depth

def hook_scipy_sparse_csgraph(finder, module):
    depth = getattr(finder,"recursion_depth_sparse",0)
    if depth==0:
        finder.recursion_depth_sparse = depth + 1
        finder.import_hook("scipy.sparse.csgraph._validation")
        finder.import_hook("scipy")
        finder.recursion_depth_sparse = depth

def hook_scipy_optimize(finder, module):
    depth = getattr(finder,"recursion_depth_optimize",0)
    if depth==0:
        finder.recursion_depth_optimize = depth + 1
        finder.import_hook("scipy.optimize.minpack2")
        finder.import_hook("scipy")
        finder.recursion_depth_optimize = depth

def hook_selenium(finder, module):
    from pathlib import Path

    import selenium

    # add all *.js data files in the zip archive
    for path in Path(selenium.__file__).parent.rglob('*.js'):
        sep = path.parts.index('selenium')
        name = str(Path(*path.parts[sep:]))
        finder.add_datafile_to_zip(name, path)

def hook_shapely(finder, module):
    import glob
    import shapely
    for dll_path in glob.glob(os.path.join(os.path.abspath(os.path.join(os.path.dirname(shapely.__file__), 'DLLs')), '*.dll')):
        finder.add_dll(dll_path)

def hook__ssl(finder, module):
    """
    On Python 3.7 and above, _ssl.pyd requires additional dll's to load.
    Based on code by Sebastian Krause: https://github.com/anthony-tuininga/cx_Freeze/pull/470
    Apparently, even with the new DLL finder system, this hook is still needed on cp37-win32
    """
    if sys.version_info < (3, 7, 0):
        return

    import glob
    for dll_search in ["libcrypto-*.dll", "libssl-*.dll"]:
        for dll_path in glob.glob(os.path.join(sys.base_prefix, "DLLs", dll_search)):
            dll_name = os.path.basename(dll_path)
            finder.add_dll(dll_path)

def hook_wx(finder, module):
    """
    Avoid `wxPyDeprecationWarning: wx.lib.pubsub has been deprecated` and
    `RuntimeError: Should not import this directly, used by pubsub.core if applicable`
    when importing the full wx package
    """
    finder.excludes.append("wx.lib.pubsub")

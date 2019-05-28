// Need to define these to be able to use SetDllDirectory.
#define _WIN32_WINNT 0x0502
#define NTDDI_VERSION 0x05020000
#include <Python.h>
#include <windows.h>

static char module_doc[] =
"Importer which can load extension modules from memory";

#include "MyLoadLibrary.h"
#include "actctx.h"
#include "python-dynload.h"

/*
static int dprintf(char *fmt, ...)
{
	char Buffer[4096];
	va_list marker;
	int result;

	va_start(marker, fmt);
	result = vsprintf(Buffer, fmt, marker);
	OutputDebugString(Buffer);
	return result;
}
*/

#if (PY_VERSION_HEX >= 0x03030000)

/* Magic for extension modules (built-in as well as dynamically
   loaded).  To prevent initializing an extension module more than
   once, we keep a static dictionary 'extensions' keyed by the tuple
   (module name, module name)  (for built-in modules) or by
   (filename, module name) (for dynamically loaded modules), containing these
   modules.  A copy of the module's dictionary is stored by calling
   _PyImport_FixupExtensionObject() immediately after the module initialization
   function succeeds.  A copy can be retrieved from there by calling
   _PyImport_FindExtensionObject().

   Modules which do support multiple initialization set their m_size
   field to a non-negative number (indicating the size of the
   module-specific state). They are still recorded in the extensions
   dictionary, to avoid loading shared libraries twice.
*/


/* c:/users/thomas/devel/code/cpython-3.4/Python/importdl.c 73 */

int do_import(FARPROC init_func, char *modname)
{
	int res = -1;
	PyObject* (*p)(void);
	PyObject *m = NULL;
	struct PyModuleDef *def;
	char *oldcontext;
	PyObject *name = PyUnicode_FromString(modname);

	if (name == NULL)
		return -1;

	m = _PyImport_FindExtensionObject(name, name);
	if (m != NULL) {
		Py_DECREF(name);
		return 0;
	}

	if (init_func == NULL) {
		PyObject *msg = PyUnicode_FromFormat("dynamic module does not define "
						     "init function (PyInit_%s)",
						     modname);
		if (msg != NULL) {
			PyErr_SetImportError(msg, name, NULL);
			Py_DECREF(msg);
		}
		Py_DECREF(name);
		return -1;
	}

        oldcontext = _Py_PackageContext;
	_Py_PackageContext = modname;

	p = (PyObject*(*)(void))init_func;
	m = (*p)();

	_Py_PackageContext = oldcontext;


	if (PyErr_Occurred()) {
		Py_DECREF(name);
		return -1;
	}

	/* Remember pointer to module init function. */
	def = PyModule_GetDef(m);
	if (def == NULL) {
		PyObject *msg = PyUnicode_FromFormat(
			"initialization of %s did not return an extension module",
			modname);
		if (msg) {
			PyErr_SetObject(PyExc_SystemError, msg);
			Py_DECREF(msg);
		}
		Py_DECREF(name);
		return -1;
	}
	def->m_base.m_init = p;

    #if (PY_VERSION_HEX >= 0x03070000)

    PyObject *modules = NULL;
    modules = PyImport_GetModuleDict();
    res = _PyImport_FixupExtensionObject(m, name, name, modules);

    #else

    res = _PyImport_FixupExtensionObject(m, name, name);

    #endif

    Py_DECREF(name);
	return res;
}

#else
# error "Python 3.0, 3.1, and 3.2 are not supported"

#endif

extern wchar_t dirname[]; // executable/dll directory

static PyObject *
import_module(PyObject *self, PyObject *args)
{
	char *initfuncname;
	char *modname;
	char *pathname;
	HMODULE hmem;
	FARPROC init_func;

	ULONG_PTR cookie = 0;
	PyObject *findproc;
	BOOL res;

	//	MessageBox(NULL, "ATTACH", "NOW", MB_OK);
	//	DebugBreak();

	/* code, initfuncname, fqmodulename, path */
	if (!PyArg_ParseTuple(args, "sssO:import_module",
			      &modname, &pathname,
			      &initfuncname,
			      &findproc))
		return NULL;
    
	cookie = _My_ActivateActCtx(); // some windows manifest magic...
	/*
	 * The following problem occurs when we are a ctypes COM dll server
	 * build with bundle_files == 1 which uses dlls that are not in the
	 * library.zip. sqlite3.dll is such a DLL - py2exe copies it into the
	 * exe/dll directory.
	 *
	 * The COM dll server is in some directory, but the client exe is
	 * somewhere else.  So, the dll server directory is NOT on th default
	 * dll search path.
	 *
	 * We use SetDllDirectory(dirname) to add the dll server directory to
	 * the search path. Which works fine.  However, SetDllDirectory(NULL)
	 * restores the DEFAULT dll search path; so it may remove directories
	 * the the client has installed.  Do we have to call GetDllDirectory()
	 * and save the result to be able to restore the path afterwards
	 * again?
	 *
	 * Best would probably be to use AddDllDirectory / RemoveDllDirectory
	 * but these are not even available by default on windows7...
	 *
	 * Are there other ways to allow loading of these dlls?  Application manifests?
	 *
	 * What about this activation context stuff?
	 *
	 * Note: py2exe 0.6 doesn't have this problem since it packs the
	 * sqlite3.dll into the zip-archve when bundle_files == 1, but we want
	 * to avoid that since it fails for other dlls (libiomp5.dll from
	 * numpy is such an example).
	 */
	res = SetDllDirectoryW(dirname); // Add a directory to the search path
	hmem = MyLoadLibrary(pathname, NULL, findproc);
	if (res)
		SetDllDirectory(NULL); // restore the default dll directory search path
	_My_DeactivateActCtx(cookie);

	if (!hmem) {
	        char *msg;
		PyObject *error;
		FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
			       NULL,
			       GetLastError(),
			       MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
			       (void *)&msg,
			       0,
			       NULL);
		msg[strlen(msg)-2] = '\0';
		error = PyUnicode_FromFormat("MemoryLoadLibrary failed loading %s: %s (%d)",
					     pathname, msg, GetLastError());
		if (error) {
			PyErr_SetObject(PyExc_ImportError, error);
			Py_DECREF(error);
		} else {
			PyErr_Clear();
			PyErr_SetString(PyExc_ImportError, "foobar");
		}
		LocalFree(msg);
		return NULL;
	}

	init_func = MyGetProcAddress(hmem, initfuncname);
	if (do_import(init_func, modname) < 0) {
		MyFreeLibrary(hmem);
		return NULL;
	}

	/* Retrieve from sys.modules */
	return PyImport_ImportModule(modname);
}

static PyObject *
get_verbose_flag(PyObject *self, PyObject *args)
{
	return PyLong_FromLong(Py_VerboseFlag);
}

static PyMethodDef methods[] = {
	{ "import_module", import_module, METH_VARARGS,
	  "import_module(modname, pathname, initfuncname, finder) -> module" },
	{ "get_verbose_flag", get_verbose_flag, METH_NOARGS,
	  "Return the Py_Verbose flag" },
	{ NULL, NULL },		/* Sentinel */
};

static struct PyModuleDef moduledef = {
	PyModuleDef_HEAD_INIT,
	"_memimporter", /* m_name */
	module_doc, /* m_doc */
	-1, /* m_size */
	methods, /* m_methods */
	NULL, /* m_reload */
	NULL, /* m_traverse */
	NULL, /* m_clear */
	NULL, /* m_free */
};


PyMODINIT_FUNC PyInit__memimporter(void)
{
	return PyModule_Create(&moduledef);
}

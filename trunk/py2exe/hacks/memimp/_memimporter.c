#include "Python.h"
#include <windows.h>

static char module_doc[] =
"Importer which can load extension modules from memory";

#include "MemoryModule.h"

static void *memdup(void *ptr, int size)
{
	void *p = malloc(size);
	if (p == NULL)
		return NULL;
	memcpy(p, ptr, size);
	return p;
}

static void* FindLibrary(char *name, PyObject *callback)
{
	PyObject *result;
	if (callback == NULL)
		return NULL;
	result = PyObject_CallFunction(callback, "s", name);
	if (result == NULL) {
		PyErr_Print();
		return NULL;
	} else if (PyString_Check(result)) {
		void *p = memdup(PyString_AS_STRING(result), PyString_GET_SIZE(result));
		Py_DECREF(result);
		return p;
	}
	return NULL;
}

static PyObject *
import_module(PyObject *self, PyObject *args)
{
	char *data;
	int size;
	char *initfuncname;
	char *fullname;
	PyObject *callback = NULL;
	HMEMORYMODULE hmem;
	FARPROC do_init;

	if (!PyArg_ParseTuple(args, "s#ss|O:import_module", &data, &size,
			      &initfuncname, &fullname, &callback))
		return NULL;
	hmem = MemoryLoadLibrary(fullname, data, FindLibrary, callback);
	if (!hmem) {
		PyErr_Format(PyExc_ImportError,
			     "MemoryLoadLibrary failed loading %s", fullname);
		return NULL;
	}
	do_init = MemoryGetProcAddress(hmem, initfuncname);
	if (!do_init) {
		MemoryFreeLibrary(hmem);
		PyErr_Format(PyExc_ImportError,
			     "Could not find function %s", initfuncname);
	}
	do_init();
	/* Retrieve from sys.modules */
	return PyImport_ImportModule(initfuncname + 4);
}

static PyObject *
get_verbose_flag(PyObject *self, PyObject *args)
{
	return PyInt_FromLong(Py_VerboseFlag);
}

static PyObject *
py_MemoryLoadLibrary(PyObject *self, PyObject *args)
{
	char *name;
	void *data;
	int len;
	PyObject *callback = NULL;

	if (!PyArg_ParseTuple(args, "ss#|O", &name, &data, &len, &callback))
		return NULL;
	return PyLong_FromVoidPtr(MemoryLoadLibrary(name, data, FindLibrary, callback));
}

static PyObject *
py_LoadLibrary(PyObject *self, PyObject *args)
{
	char *name;
	PyObject *callback = NULL;

	if (!PyArg_ParseTuple(args, "s|O", &name, &callback))
		return NULL;
	return PyLong_FromVoidPtr(MyLoadLibrary(name, FindLibrary, callback));
}

static PyObject *
py_FreeLibrary(PyObject *self, PyObject *args)
{
	HMODULE handle;
	if (!PyArg_ParseTuple(args, "i", &handle))
		return NULL;
	return PyBool_FromLong(MyFreeLibrary(handle));
}

static PyMethodDef methods[] = {
	{ "import_module", import_module, METH_VARARGS,
	  "import_module(code, initfunc, dllname) -> module" },
	{ "get_verbose_flag", get_verbose_flag, METH_NOARGS,
	  "Return the Py_Verbose flag" },
	{ "LoadLibrary", py_LoadLibrary, METH_VARARGS },
	{ "FreeLibrary", py_FreeLibrary, METH_VARARGS },
	{ "MemoryLoadLibrary", py_MemoryLoadLibrary, METH_VARARGS },
	{ NULL, NULL },		/* Sentinel */
};

DL_EXPORT(void)
init_memimporter(void)
{
	Py_InitModule3("_memimporter", methods, module_doc);
}

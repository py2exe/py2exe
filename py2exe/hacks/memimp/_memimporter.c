#include "../../source/Python-dynload.h"
#include <windows.h>
#include <stdio.h>

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

/* Behaviour with errors is somewhat weird... */
static void* FindLibrary(char *name, PyObject *callback)
{
	PyObject *result;
	char *p;
	int size;

	if (callback == NULL)
		return NULL;
	result = PyObject_CallFunction(callback, "s", name);
	if (result == NULL) {
		PyErr_Print();
		return NULL;
	}
	if (-1 == PyString_AsStringAndSize(result, &p, &size)) {
		Py_DECREF(result);
		return NULL;
	}
	p = memdup(p, size);
	Py_DECREF(result);
	return p;
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

static PyMethodDef methods[] = {
	{ "import_module", import_module, METH_VARARGS,
	  "import_module(code, initfunc, dllname[, finder]) -> module" },
	{ "get_verbose_flag", get_verbose_flag, METH_NOARGS,
	  "Return the Py_Verbose flag" },
	{ NULL, NULL },		/* Sentinel */
};

DL_EXPORT(void)
init_memimporter(void)
{
	Py_InitModule3("_memimporter", methods, module_doc);
}

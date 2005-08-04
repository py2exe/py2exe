/*
  For the _memimporter compiled into py2exe exe-stubs we need "Python-dynload.h".
  For the standalone .pyd we need <Python.h>
*/

#ifdef STANDALONE
#  include <Python.h>
#else
#  include "Python-dynload.h"
#  include <stdio.h>
#endif

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

/*
  Be sure to detect errors in FindLibrary - undetected errors lead to
  very strange bahaviour.
*/
static void* FindLibrary(char *name, PyObject *callback)
{
	PyObject *result;
	char *p;
	int size;

	if (callback == NULL)
		return NULL;
	result = PyObject_CallFunction(callback, "s", name);
	if (result == NULL) {
		PyErr_Clear();
		return NULL;
	}
	if (-1 == PyString_AsStringAndSize(result, &p, &size)) {
		PyErr_Clear();
		Py_DECREF(result);
		return NULL;
	}
	p = memdup(p, size);
	Py_DECREF(result);
	return p;
}

static PyObject *set_find_proc(PyObject *self, PyObject *args)
{
	PyObject *callback = NULL;
	if (!PyArg_ParseTuple(args, "|O:set_find_proc", &callback))
		return NULL;
	Py_XDECREF((PyObject *)findproc_data);
	Py_XINCREF(callback);
	findproc_data = (void *)callback;
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
import_module(PyObject *self, PyObject *args)
{
	char *data;
	int size;
	char *initfuncname;
	char *fullname;
	HMEMORYMODULE hmem;
	FARPROC do_init;

	if (!PyArg_ParseTuple(args, "s#ss:import_module", &data, &size,
			      &initfuncname, &fullname))
		return NULL;
	hmem = MemoryLoadLibrary(fullname, data);
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
	{ "set_find_proc", set_find_proc, METH_VARARGS },
	{ NULL, NULL },		/* Sentinel */
};

DL_EXPORT(void)
init_memimporter(void)
{
	findproc = FindLibrary;
	Py_InitModule3("_memimporter", methods, module_doc);
}

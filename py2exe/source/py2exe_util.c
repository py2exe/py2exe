#include "Python.h"
#include <windows.h>
#include <imagehlp.h>

static char module_doc[] =
"Utility functions for the py2exe package";

static char* searchpath;
static PyListObject *py_result;

static void SystemError(int error)
{
    LPVOID lpMsgBuf;
    FormatMessage( 
	FORMAT_MESSAGE_ALLOCATE_BUFFER | 
	FORMAT_MESSAGE_FROM_SYSTEM,
	NULL,
	error,
	MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
	(LPSTR)&lpMsgBuf,
	0,
	NULL 
	);
    PyErr_SetString(PyExc_RuntimeError, lpMsgBuf);
    LocalFree(lpMsgBuf);
}

BOOL __stdcall StatusRoutine(IMAGEHLP_STATUS_REASON reason,
			  PSTR ImageName,
			  PSTR DllName,
			  ULONG Va,
			  ULONG Parameter)
{
    DWORD result;

    char fname[_MAX_PATH+1];

    switch(reason) {
    case BindOutOfMemory:
    case BindRvaToVaFailed:
    case BindNoRoomInImage:
    case BindImportProcedureFailed:
    case BindImportProcedure:
    case BindForwarder:
    case BindForwarderNOT:
    case BindImageModified:
    case BindExpandFileHeaders:
    case BindImageComplete:
    case BindSymbolsNotUpdated:
    case BindMismatchedSymbols:
	break;

    case BindImportModuleFailed:
    case BindImportModule:
	if (!py_result)
	    return FALSE;
	result = SearchPath(searchpath, DllName, NULL, sizeof(fname), fname, NULL);
	if (result)
	    PyList_Append((PyObject *)py_result, PyString_FromString(fname));
	else
	    PyList_Append((PyObject *)py_result, PyString_FromString(DllName));
	break;
    }
    return TRUE;
}

static PyObject *depends(PyObject *self, PyObject *args)
{
    char *imagename;
    PyListObject *plist;
    HINSTANCE hLib;
    BOOL(__stdcall *pBindImageEx)(
	DWORD Flags,
	LPSTR ImageName,
	LPSTR DllPath,
	LPSTR SymbolPath,
	PIMAGEHLP_STATUS_ROUTINE StatusRoutine
    );

    searchpath = NULL;

    if (!PyArg_ParseTuple(args, "s|s", &imagename, &searchpath))
	return NULL;
    hLib = LoadLibrary("imagehlp");
    if (!hLib) {
	PyErr_SetString(PyExc_SystemError,
			"imagehlp.dll not found");
	return NULL;
    }
    pBindImageEx = (FARPROC)GetProcAddress(hLib, "BindImageEx");
    if (!pBindImageEx) {
	PyErr_SetString(PyExc_SystemError,
			"imagehlp.dll does not export BindImageEx function");
	FreeLibrary(hLib);
	return NULL;
    }

    py_result = (PyListObject *)PyList_New(0);
    if (!pBindImageEx(BIND_NO_BOUND_IMPORTS | BIND_NO_UPDATE | BIND_ALL_IMAGES,
		     imagename,
		     searchpath,
		     NULL,
		     StatusRoutine)) {
	FreeLibrary(hLib);
	Py_DECREF(py_result);
	PyErr_SetString(PyExc_RuntimeError, "could not bind");
	return NULL;
    }
    FreeLibrary(hLib);
    plist = py_result;
    py_result = NULL;
    return (PyObject *)plist;
}

static PyObject *get_windir(PyObject *self, PyObject *args)
{
    char windir[_MAX_PATH];
    if (!PyArg_ParseTuple(args, ""))
	return NULL;
    if (GetWindowsDirectory(windir, sizeof(windir)))
	return PyString_FromString(windir);
    PyErr_SetString(PyExc_RuntimeError, "could not get windows directory");
    return NULL;
}

static PyObject *get_sysdir(PyObject *self, PyObject *args)
{
    char sysdir[_MAX_PATH];
    if (!PyArg_ParseTuple(args, ""))
	return NULL;
    if (GetSystemDirectory(sysdir, sizeof(sysdir)))
	return PyString_FromString(sysdir);
    PyErr_SetString(PyExc_RuntimeError, "could not get system directory");
    return NULL;
}

static PyMethodDef methods[] = {
    { "get_sysdir", get_sysdir, METH_VARARGS,
      "get_sysdir() - Return the windows system directory"},
    { "get_windir", get_windir, METH_VARARGS,
      "get_windir() - Return the windows directory"},
    { "depends", depends, METH_VARARGS,
      "depends(executable[, loadpath]) -> list\n\n"
      "Return a list containing the dlls needed to run 'executable'.\n"
      "The dlls are searched along 'loadpath'\n"
      "or windows default loadpath", },
    { NULL, NULL },		/* Sentinel */
};

DL_EXPORT(void)
initpy2exe_util(void)
{
    Py_InitModule3("py2exe_util", methods, module_doc);
}

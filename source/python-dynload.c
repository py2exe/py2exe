#include <Python.h>
#include <windows.h>
#include "MyLoadLibrary.h"
#include "python-dynload.h"

/*
  This module allows us to dynamically load the python DLL.

  We have to #define Py_BUILD_CORE when we cmpile our stuff,
  then the exe doesn't try to link with pythonXY.lib, and also
  the following definitions compile.

  We use MyGetProcAddress to get the functions from the dynamically
  loaded python DLL, so it will work both with the DLL loaded from the
  file system as well as loaded from memory.

  Problems:
  - We cannot use vararg functions that have no va_list counterpart.
  - What about the flags or other data exported from Python?
  - Error handling MUST be improved...
  - Should we use a python script to generate this code
    from function prototypes automatically?
*/

static HMODULE hmod_pydll;

/*
  The python dll may be loaded from memory or in the usual way.
  MyGetProcAddress handles both cases.
*/

#define FUNC(res, name, args) \
  static res(*proc)args; \
  if (!proc) (FARPROC)proc = MyGetProcAddress(hmod_pydll, #name)

#define DATA(type, name)				\
  static type pflag; \
  if (!pflag) pflag = (type)MyGetProcAddress(hmod_pydll, #name); \
  return pflag

////////////////////////////////////////////////////////////////

int *_Py_OptimizeFlag_PTR()
{
  DATA(int *, Py_OptimizeFlag);
}

int *_Py_NoSiteFlag_PTR()
{
  DATA(int *, Py_NoSiteFlag);
}

int *_Py_VerboseFlag_PTR()
{
  DATA(int *, Py_VerboseFlag);
}

char **__Py_PackageContext_PTR()
{
  DATA(char **, _Py_PackageContext);
}

////////////////////////////////////////////////////////////////

int Py_IsInitialized(void)
{
  FUNC(int, Py_IsInitialized, (void));
  return proc();
}

PyObject *PyLong_FromVoidPtr(void *p)
{
  FUNC(PyObject *, PyLong_FromVoidPtr, (void *));
  return proc(p);
}

PyObject *PyErr_SetImportError(PyObject *msg, PyObject *name, PyObject *path)
{
  FUNC(PyObject *, PyErr_SetImportError, (PyObject *, PyObject *, PyObject *));
  return proc(msg, name, path);
}

void PyErr_SetString(PyObject *type, const char *message)
{
  FUNC(void, PyErr_SetString, (PyObject *, const char *));
  proc(type, message);
}

int Py_FdIsInteractive(FILE *fp, const char *filename)
{
  FUNC(int, Py_FdIsInteractive, (FILE *, const char *));
  return proc(fp, filename);
}

int PyRun_InteractiveLoopFlags(FILE *fp, const char *filename, PyCompilerFlags *flags)
{
  FUNC(int, PyRun_InteractiveLoopFlags, (FILE *, const char *, PyCompilerFlags *));
  return proc(fp, filename, flags);
}

int PyRun_SimpleStringFlags(const char *command, PyCompilerFlags *flags)
{
  FUNC(int, PyRun_SimpleStringFlags, (const char *, PyCompilerFlags *));
  return proc(command, flags);
}

void PyGILState_Release(PyGILState_STATE state)
{
  FUNC(void, PyGILState_Release, (PyGILState_STATE));
  proc(state);
}

PyGILState_STATE PyGILState_Ensure(void)
{
  FUNC(PyGILState_STATE, PyGILState_Ensure, (void));
  return proc();
}

wchar_t *Py_GetPath(void)
{
  FUNC(wchar_t *, Py_GetPath, (void));
  return proc();
}

void Py_SetPath(const wchar_t *path)
{
  FUNC(void, Py_SetPath, (const wchar_t *));
  proc(path);
}

void Py_Finalize(void)
{
  FUNC(void, Py_Finalize, (void));
  proc();
}

void Py_Initialize(void)
{
  FUNC(void, Py_Initialize, (void));
  proc();
}

void PyErr_Clear(void)
{
  FUNC(void, PyErr_Clear, (void));
  proc();
}

PyObject *PyErr_Occurred(void)
{
  FUNC(PyObject *, PyErr_Occurred, (void));
  return proc();
}

void PyErr_Print(void)
{
  FUNC(void, PyErr_Print, (void));
  proc();
}

void Py_SetProgramName(wchar_t *name)
{
  FUNC(void, Py_SetProgramName, (wchar_t *));
  proc(name);
}

void PySys_SetArgvEx(int argc, wchar_t **argv, int updatepath)
{
  FUNC(void, PySys_SetArgvEx, (int, wchar_t **, int));
  proc(argc, argv, updatepath);
}

PyObject *PyImport_AddModule(const char *name)
{
  FUNC(PyObject *, PyImport_AddModule, (const char *));
  return proc(name);
}

PyObject *PyModule_GetDict(PyObject *m)
{
  FUNC(PyObject *, PyModule_GetDict, (PyObject *));
  return proc(m);
}

PyObject *PyMarshal_ReadObjectFromString(char *string, Py_ssize_t len)
{
  FUNC(PyObject *, PyMarshal_ReadObjectFromString, (char *, Py_ssize_t));
  return proc(string, len);
}

PyObject *PySequence_GetItem(PyObject *seq, Py_ssize_t i)
{
  FUNC(PyObject *, PySequence_GetItem, (PyObject *, Py_ssize_t));
  return proc(seq, i);
}

Py_ssize_t PySequence_Size(PyObject *seq)
{
  FUNC(Py_ssize_t, PySequence_Size, (PyObject *));
  return proc(seq);
}

PyObject *PyEval_EvalCode(PyObject *co, PyObject *globals, PyObject *locals)
{
  FUNC(PyObject *, PyEval_EvalCode, (PyObject *, PyObject *, PyObject *));
  return proc(co, globals, locals);
}

int PyImport_AppendInittab(const char *name, PyObject* (*initfunc)(void))
{
  FUNC(int, PyImport_AppendInittab, (const char *, PyObject *(*)(void)));
  return proc(name, initfunc);
}

PyObject *PyModule_Create2(PyModuleDef *module, int module_api_version)
{
  FUNC(PyObject *, PyModule_Create2, (PyModuleDef *, int));
  return proc(module, module_api_version);
}

PyObject *PyLong_FromLong(long n)
{
  FUNC(PyObject *, PyLong_FromLong, (long));
  return proc(n);
}

int PyArg_ParseTuple(PyObject *args, const char *format, ...)
{
  int result;
  va_list marker;
  FUNC(int, PyArg_VaParse, (PyObject *, const char *, va_list));
  va_start(marker, format);
  result = proc(args, format, marker);
  va_end(marker);
  return -1;
}

PyObject *PyUnicode_FromFormat(const char *format, ...)
{
  PyObject *result;
  va_list marker;
  FUNC(PyObject *, PyUnicode_FromFormatV, (const char *, va_list));
  va_start(marker, format);
  result = proc(format, marker);
  va_end(marker);
  return result;
}

PyObject *PyUnicode_FromWideChar(const wchar_t *w, Py_ssize_t size)
{
  FUNC(PyObject *, PyUnicode_FromWideChar, (const wchar_t *, Py_ssize_t));
  return proc(w, size);
}

PyObject *PyObject_CallObject(PyObject *callable, PyObject *args)
{
  FUNC(PyObject *, PyObject_CallObject, (PyObject *, PyObject *));
  return proc(callable, args);
}

PyObject *PyTuple_New(Py_ssize_t len)
{
  FUNC(PyObject *, PyTuple_New, (Py_ssize_t));
  return proc(len);
}

int PyTuple_SetItem(PyObject *p, Py_ssize_t pos, PyObject *o)
{
  FUNC(int, PyTuple_SetItem, (PyObject *, Py_ssize_t, PyObject *));
  return proc(p, pos, o);
}

PyObject *PyUnicode_FromString(const char *u)
{
  FUNC(PyObject *, PyUnicode_FromString, (const char *));
  return proc(u);
}

#undef _Py_Dealloc

void _Py_Dealloc(PyObject *op)
{
    destructor dealloc = Py_TYPE(op)->tp_dealloc;
#ifdef Py_TRACE_REFS
    _Py_ForgetReference(op);
#else
  #if (PY_VERSION_HEX < 0x03090000)
    _Py_INC_TPFREES(op);
  #endif
#endif
    (*dealloc)(op);
}

char *PyBytes_AsString(PyObject *string)
{
  FUNC(char *, PyBytes_AsString, (PyObject *));
  return proc(string);
}

PyModuleDef *PyModule_GetDef(PyObject *module)
{
  FUNC(PyModuleDef *, PyModule_GetDef, (PyObject *));
  return proc(module);
}

#if (PY_VERSION_HEX >= 0x03070000)

PyObject *PyImport_GetModuleDict(void)
{
  FUNC(PyObject *, PyImport_GetModuleDict, (void));
  return proc();
}

#endif

PyObject *PyImport_ImportModule(const char *name)
{
  FUNC(PyObject *, PyImport_ImportModule, (const char *));
  return proc(name);
}

PyObject *_PyImport_FindExtensionObject(PyObject *a, PyObject *b)
{
  FUNC(PyObject *, _PyImport_FindExtensionObject, (PyObject *, PyObject *));
  return proc(a, b);
}

#if (PY_VERSION_HEX >= 0x03070000)

int _PyImport_FixupExtensionObject(PyObject *m, PyObject *a, PyObject *b, PyObject *l)
{
  FUNC(int, _PyImport_FixupExtensionObject, (PyObject *, PyObject *, PyObject *, PyObject *));
  return proc(m, a, b, l);
}

#else

int _PyImport_FixupExtensionObject(PyObject *m, PyObject *a, PyObject *b)
{
    FUNC(int, _PyImport_FixupExtensionObject, (PyObject *, PyObject *, PyObject *));
    return proc(m, a, b);
}

#endif


int PySys_SetObject(const char *name, PyObject *v)
{
  FUNC(int, PySys_SetObject, (const char *, PyObject *));
  return proc(name, v);
}

void PyErr_SetObject(PyObject *type, PyObject *value)
{
  FUNC(PyObject *, PyErr_SetObject, (PyObject *, PyObject *));
  proc(type, value);
}

PyObject *PyBool_FromLong(long v)
{
  FUNC(PyObject *, PyBool_FromLong, (long));
  return proc(v);
}

int PyObject_SetAttrString(PyObject *o, const char *attr_name, PyObject *v)
{
  FUNC(int, PyObject_SetAttrString, (PyObject *, const char *, PyObject *));
  return proc(o, attr_name, v);
}

#if (PY_VERSION_HEX < 0x03090000)

PyObject *PyCFunction_NewEx(PyMethodDef *methdef, PyObject *self, PyObject *foo)
{
  FUNC(PyObject *, PyCFunction_NewEx, (PyMethodDef *, PyObject *, PyObject *));
  return proc(methdef, self, foo);
}

#endif

#if (PY_VERSION_HEX >= 0x03090000)

PyObject *PyCMethod_New(PyMethodDef *ml, PyObject *self, PyObject *module, PyTypeObject *cls)
{
  FUNC(PyObject *, PyCMethod_New, (PyMethodDef *, PyObject *, PyObject *, PyTypeObject *));
  return proc(ml, self, module, cls);

}

#endif

////////////////////////////////////////////////////////////////

int PythonLoaded(HMODULE hmod)
{
  hmod_pydll = hmod;
  PyExc_SystemError = *((PyObject **)MyGetProcAddress(hmod, "PyExc_SystemError"));
  if (PyExc_SystemError == NULL)
    return -1;
  PyExc_ImportError = *((PyObject **)MyGetProcAddress(hmod, "PyExc_ImportError"));
  if (PyExc_ImportError == NULL)
    return -1;
  PyExc_RuntimeError = *((PyObject **)MyGetProcAddress(hmod, "PyExc_RuntimeError"));
  if (PyExc_RuntimeError == NULL)
    return -1;
  return 0;
}

PyObject *PyExc_SystemError;
PyObject *PyExc_ImportError;
PyObject *PyExc_RuntimeError;

//Py_VerboseFlag

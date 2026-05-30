/*
 * This file is needed because in Python3.13+ some exported symbols
 * inside of import.c that are not part of cpython's stable ABI were
 * removed entirely. As such import_mini.c adds the removed ABI back,
 * but ported to use the stable ABI as much as possible for support
 * on future versions of cpython.
 */
#pragma once

#if !defined(Py_BUILD_CORE_BUILTIN) && !defined(Py_BUILD_CORE_MODULE)
#define Py_BUILD_CORE_MODULE 1
#endif

#include <Python.h>

/* Work around not being able to use _Py_PackageContext in Python 3.12+. */
#if (PY_VERSION_HEX >= 0x030C0000)
#include <internal/pycore_runtime.h>
#include <internal/pycore_pystate.h>
#endif

#if (PY_VERSION_HEX >= 0x030D00B0)
int _PyImport_FixupExtensionObject(PyObject *m, PyObject *name1, PyObject *name2, PyObject *modules);
#endif

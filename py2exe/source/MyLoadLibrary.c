#ifdef STANDALONE
#  include <Python.h>
#  include "Python-version.h"
#else
#  include "Python-dynload.h"
#  include <stdio.h>
#endif
#include <windows.h>

#include "MemoryModule.h"
#include "MyLoadLibrary.h"

/*

Windows API:
============

HMODULE LoadLibraryA(LPCSTR)
HMODULE GetModuleHandleA(LPCSTR)
BOOL FreeLibrary(HMODULE)
FARPROC GetProcAddress(HMODULE, LPCSTR)


MemoryModule API:
=================

HMEMORYMODULE MemoryLoadLibrary(void *)
void MemoryFreeLibrary(HMEMORYMODULE)
FARPROC MemoryGetProcAddress(HMEMORYMODULE, LPCSTR)

HMEMORYMODULE MemoryLoadLibrayEx(void *,
                                 load_func, getproc_func, free_func, userdata)

(there are also some resource functions which are not used here...)

General API in this file:
=========================

HMODULE MyLoadLibrary(LPCSTR, void *, userdata)
HMODULE MyGetModuleHandle(LPCSTR)
BOOL MyFreeLibrary(HMODULE)
FARPROC MyGetProcAddress(HMODULE, LPCSTR)

 */

/****************************************************************
 * A linked list of loaded MemoryModules.
 */
typedef struct tagLIST {
	HCUSTOMMODULE module;
	LPCSTR name;
	struct tagLIST *next;
	struct tagLIST *prev;
	int refcount;
} LIST;

static LIST *libraries;

/****************************************************************
 * Search for a loaded MemoryModule in the linked list, either by name
 * or by module handle.
 */
static LIST *_FindMemoryModule(LPCSTR name, HMODULE module)
{
	LIST *lib = libraries;
	while (lib) {
		if (name && 0 == stricmp(name, lib->name)) {
//			printf("_FindMemoryModule(%s, %p) -> %s\n", name, module, lib->name);
			return lib;
		} else if (module == lib->module) {
//			printf("_FindMemoryModule(%s, %p) -> %s\n", name, module, lib->name);
			return lib;
		} else {
			lib = lib->next;
		}
	}
//	printf("_FindMemoryModule(%s, %p) -> NULL\n", name, module);
	return NULL;
}

/****************************************************************
 * Insert a MemoryModule into the linked list of loaded modules
 */
static LIST *_AddMemoryModule(LPCSTR name, HCUSTOMMODULE module)
{
	LIST *entry = (LIST *)malloc(sizeof(LIST));
	entry->name = strdup(name);
	entry->module = module;
	entry->next = libraries;
	entry->prev = NULL;
	entry->refcount = 1;
	libraries = entry;
//	printf("_AddMemoryModule(%s, %p) -> %p\n", name, module, entry);
	return entry;
}

/****************************************************************
 * Helper functions for MemoryLoadLibraryEx
 */
static FARPROC _GetProcAddress(HCUSTOMMODULE module, LPCSTR name, void *userdata)
{
	FARPROC res;
	res = (FARPROC)GetProcAddress((HMODULE)module, name);
	if (res == NULL) {
		SetLastError(0);
		return MemoryGetProcAddress(module, name);
	} else
		return res;
}

static void _FreeLibrary(HCUSTOMMODULE module, void *userdata)
{
	LIST *lib = _FindMemoryModule(NULL, module);
	if (lib && --lib->refcount == 0)
		MemoryFreeLibrary(module);
	else
		FreeLibrary((HMODULE) module);
}

static HCUSTOMMODULE _LoadLibrary(LPCSTR filename, void *userdata)
{
	HCUSTOMMODULE result;
	LIST *lib = _FindMemoryModule(filename, NULL);
	if (lib) {
		lib->refcount += 1;
		return lib->module;
	}
	if (userdata) {
		PyObject *findproc = (PyObject *)userdata;
		PyObject *res = PyObject_CallFunction(findproc, "s", filename);
		if (res && PyString_AsString(res)) {
			result = MemoryLoadLibraryEx(PyString_AsString(res),
						     _LoadLibrary, _GetProcAddress, _FreeLibrary,
						     userdata);
			Py_DECREF(res);
			lib = _AddMemoryModule(filename, result);
			return lib->module;
		} else {
			PyErr_Clear();
		}
		PyErr_Clear();
	}
	return (HCUSTOMMODULE)LoadLibraryA(filename);
}

/****************************************************************
 * Public functions
 */
HMODULE MyGetModuleHandle(LPCSTR name)
{
	LIST *lib;
	lib = _FindMemoryModule(name, NULL);
	if (lib)
		return lib->module;
	return GetModuleHandle(name);
}

HMODULE MyLoadLibrary(LPCSTR name, void *data, void *userdata)
{
	LIST *lib;
//	printf("MyLoadLibrary(%s, %p, %p)\n", name, data, userdata);
	lib = _FindMemoryModule(name, NULL);
	if (lib) {
		++lib->refcount;
		return lib->module;
	}
	if (userdata) {
		HCUSTOMMODULE mod = _LoadLibrary(name, userdata);
		if (mod) {
			LIST *lib = _AddMemoryModule(name, mod);
			return lib->module;
		}
	} else if (data) {
		HCUSTOMMODULE mod = MemoryLoadLibraryEx(data,
							_LoadLibrary,
							_GetProcAddress,
							_FreeLibrary,
							userdata);
		if (mod) {
			LIST *lib = _AddMemoryModule(name, mod);
			return lib->module;
		}
	}
	return LoadLibrary(name);
}

BOOL MyFreeLibrary(HMODULE module)
{
	LIST *lib = _FindMemoryModule(NULL, module);
	if (lib) {
		if (--lib->refcount == 0) {
			MemoryFreeLibrary(module);
			/* remove lib entry from linked list */
		}
		return TRUE;
	} else
		return FreeLibrary(module);
}

FARPROC MyGetProcAddress(HMODULE module, LPCSTR procname)
{
	LIST *lib = _FindMemoryModule(NULL, module);
	if (lib)
		return MemoryGetProcAddress(lib->module, procname);
	else
		return GetProcAddress(module, procname);
}

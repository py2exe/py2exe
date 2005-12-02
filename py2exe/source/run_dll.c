/*
 *     Copyright (c) 2000, 2001 Thomas Heller
 *     Copyright (c) 2003 Mark Hammond
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
#include "Python-dynload.h"
#include <assert.h>
#include <windows.h>
#include <stdio.h>
#include <olectl.h>
//#include <Python.h> // XXX
#include "MemoryModule.h"

// Function pointers we load from pythoncom
typedef int (__stdcall *__PROC__DllCanUnloadNow) (void);
typedef HRESULT (__stdcall *__PROC__DllGetClassObject) (REFCLSID, REFIID, LPVOID *);
typedef void (__cdecl *__PROC__PyCom_CoUninitialize) (void);

extern BOOL _LoadPythonDLL(HMODULE hmod);
extern BOOL _LocateScript(HMODULE hmod);

CRITICAL_SECTION csInit; // protecting our init code

__PROC__DllCanUnloadNow Pyc_DllCanUnloadNow = NULL;
__PROC__DllGetClassObject Pyc_DllGetClassObject = NULL;
__PROC__PyCom_CoUninitialize PyCom_CoUninitialize = NULL;

void SystemError(int error, char *msg)
{
	char Buffer[1024];
	int n;

	if (error) {
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
		strncpy(Buffer, lpMsgBuf, sizeof(Buffer));
		LocalFree(lpMsgBuf);
	} else
		Buffer[0] = '\0';
	n = lstrlen(Buffer);
	_snprintf(Buffer+n, sizeof(Buffer)-n, msg);
	MessageBox(GetFocus(), Buffer, NULL, MB_OK | MB_ICONSTOP);
}

BOOL have_init = FALSE;
HANDLE gPythoncom = 0;
HMODULE gInstance = 0;

extern int init_with_instance(HMODULE, char *);
extern void fini();
extern int run_script(void);
extern void init_memimporter(void);

int load_pythoncom(void)
{
	char dll_path[_MAX_PATH+_MAX_FNAME+1];
	char major[35] = "x"; // itoa max size is 33.
	char minor[35] = "y";
#ifdef _DEBUG
	char *suffix = "_d";
#else
	char *suffix = "";
#endif
/*
	// no reference added by PySys_GetObject
	PyObject *ob_vi = PySys_GetObject("version_info");
	if (ob_vi && PyTuple_Check(ob_vi) && PyTuple_Size(ob_vi)>1) {
		itoa(PyInt_AsLong(PyTuple_GET_ITEM(ob_vi, 0)), major, 10);
		itoa(PyInt_AsLong(PyTuple_GET_ITEM(ob_vi, 1)), minor, 10);
	}
*/
	// shouldn't do this twice
	assert(gPythoncom == NULL);

	snprintf(dll_path, sizeof(dll_path), PYTHONCOM);
	gPythoncom = MyGetModuleHandle(dll_path);
	// GetModuleFileNameA and LoadLibraryEx would not work in single-file dlls
/*
	if (gPythoncom == NULL) {
		// not already loaded - try and load from the current dir
		char *temp;
		GetModuleFileNameA(gInstance, dll_path, sizeof(dll_path));
		temp = dll_path + strlen(dll_path);
		while (temp>dll_path && *temp != '\\')
			temp--;
		// and printf directly in the buffer.
		// don't overwrite the backslash, so temp+1!
		snprintf(temp+1, sizeof(dll_path)-strlen(temp+1),
			 "pythoncom%s%s%s.dll", major, minor, suffix);
		gPythoncom = LoadLibraryEx(dll_path, // points to name of executable module 
					   NULL, // HANDLE hFile, // reserved, must be NULL 
					   LOAD_WITH_ALTERED_SEARCH_PATH // DWORD dwFlags // entry-point execution flag 
			); 
	}
*/
	if (gPythoncom == NULL) {
		OutputDebugString("GetModuleHandle pythoncom failed");
		// give up in disgust
		return -1;
	}

	Pyc_DllCanUnloadNow = (__PROC__DllCanUnloadNow)MyGetProcAddress(gPythoncom, "DllCanUnloadNow");
	Pyc_DllGetClassObject = (__PROC__DllGetClassObject)MyGetProcAddress(gPythoncom, "DllGetClassObject");
	PyCom_CoUninitialize = (__PROC__PyCom_CoUninitialize)MyGetProcAddress(gPythoncom, "PyCom_CoUninitialize");
	return 0;
}

/* for debugging
#define ODS(s) OutputDebugString(s)

static int dprintf(char *fmt, ...)
{
	char Buffer[4096];
	va_list marker;
	int result;
	
	va_start(marker, fmt);
	result = wvsprintf(Buffer, fmt, marker);
	OutputDebugString(Buffer);
	return result;
}
*/

int check_init()
{
	if (!have_init) {
		EnterCriticalSection(&csInit);
		// Check the flag again - another thread may have beat us to it!
		if (!have_init) {
			PyObject *frozen;
			/* Consider a py2exe generated COM DLL, and a py2exe
			   generated .EXE that makes use of the COM object (both
			   in the same distribution)

			   When VB, for example, creates the COM object, this
			   code has not previously loaded Python. Python is
			   therefore not initialized, so a normal Python init
			   routine works fine.

			   However - consider when our .exe attempts to create
			   the COM object. Python has already been initialized
			   in this process (as the .exe started up), but the
			   function pointers (eg, Py_IsInitialized) are yet to
			   be loaded in this DLLs private data. Worse, in this
			   case the GIL is not held, so calling
			   init_with_instance in this state will do things like
			   call PySys_SetObject, which will abort() as there is
			   no thread-state.

			   In all cases, we must exit this function with the GIL
			   released.
			*/
			PyGILState_STATE restore_state = PyGILState_UNLOCKED;
			/* Before we call Python functions, we must make sure
			   that the python dll is loaded - we are loading it
			   at runtime now.  MyGetModuleHandle() should work,
			   but we can aso check if the functions are
			   available.
			 */
			if (!Py_IsInitialized) {
				// Python function pointers are yet to be loaded
				// - force that now. See above for why we *must*
				// know about the initialized state of Python so
				// we can setup the thread-state correctly
				// before calling init_with_instance(); This is
				// wasteful, but fixing it would involve a
				// restructure of init_with_instance()
				_LocateScript(gInstance);
				_LoadPythonDLL(gInstance);
			}
			if (Py_IsInitialized && Py_IsInitialized()) {
				restore_state = PyGILState_Ensure();
			}
			// a little DLL magic.  Set sys.frozen='dll'
			init_with_instance(gInstance, "dll");
			init_memimporter();
			frozen = PyInt_FromLong((LONG)gInstance);
			if (frozen) {
				PySys_SetObject("frozendllhandle", frozen);
				Py_DECREF(frozen);
			}
			// Now run the generic script - this always returns in a DLL.
			run_script();
			have_init = TRUE;
			if (gPythoncom == NULL)
				load_pythoncom();
			// Reset the thread-state, so any thread can call in
			PyGILState_Release(restore_state);
		}
		LeaveCriticalSection(&csInit);
	}
	return gPythoncom != NULL;
}


// *****************************************************************
// All the public entry points needed for COM, Windows, and anyone
// else who wants their piece of the action.
// *****************************************************************
BOOL WINAPI DllMain(HINSTANCE hInstance, DWORD dwReason, LPVOID lpReserved)
{
	if ( dwReason == DLL_PROCESS_ATTACH) {
		gInstance = hInstance;
		InitializeCriticalSection(&csInit);
	}
	else if ( dwReason == DLL_PROCESS_DETACH ) {
		gInstance = 0;
		DeleteCriticalSection(&csInit);
		// not much else safe to do here
	}
	return TRUE; 
}

HRESULT __stdcall DllCanUnloadNow(void)
{
	HRESULT rc;
	check_init();
	assert(Pyc_DllCanUnloadNow);
	if (!Pyc_DllCanUnloadNow) return E_UNEXPECTED;
	rc = Pyc_DllCanUnloadNow();
	//if (rc == S_OK && PyCom_CoUninitialize)
	//  PyCom_CoUninitialize();
	return rc;
}

//__declspec(dllexport) int __stdcall DllGetClassObject(void *rclsid, void *riid, void *ppv)
HRESULT __stdcall DllGetClassObject(REFCLSID rclsid, REFIID riid, LPVOID *ppv)
{
	HRESULT rc;
	check_init();
	assert(Pyc_DllGetClassObject);
	if (!Pyc_DllGetClassObject) return E_UNEXPECTED;
	rc = Pyc_DllGetClassObject(rclsid, riid, ppv);
	return rc;
}


STDAPI DllRegisterServer()
{
	int rc=0;
	PyGILState_STATE state;
	check_init();
	state = PyGILState_Ensure();
	rc = PyRun_SimpleString("DllRegisterServer()\n");
	if (rc != 0)
		PyErr_Print();
	PyGILState_Release(state);
	return rc==0 ? 0 : SELFREG_E_CLASS;
}

STDAPI DllUnregisterServer()
{
	int rc=0;
	PyGILState_STATE state;
	check_init();
	state = PyGILState_Ensure();
	rc = PyRun_SimpleString("DllUnregisterServer()\n");
	if (rc != 0)
		PyErr_Print();
	PyGILState_Release(state);
	return rc==0 ? 0 : SELFREG_E_CLASS;
}

STDAPI DllInstall(BOOL install, LPCWSTR cmdline)
{
	PyObject *m = NULL, *func = NULL, *args = NULL, *result = NULL;
	PyGILState_STATE state;
	int rc=SELFREG_E_CLASS;
	check_init();
	state = PyGILState_Ensure();
	m = PyImport_AddModule("__main__");
	if (!m) goto done;
	func = PyObject_GetAttrString(m, "DllInstall");
	if (!func) goto done;
	args = Py_BuildValue("(Oi)", install ? 1 : 0, cmdline);
	if (!args) goto done;
	result = PyObject_Call(func, args, NULL);
	if (result==NULL) goto done;
	rc = 0;
	/* but let them return a custom rc (even though we don't above!) */
	if (PyInt_Check(result))
		rc = PyInt_AsLong(result);
	else if (result == Py_None)
		; /* do nothing */
	else
		/* We cannot access internals of PyObject anymore */
		PySys_WriteStderr("Unexpected return type for DllInstall\n");
//						  result->ob_type->tp_name);
done:
	if (PyErr_Occurred()) {
		PyErr_Print();
		PyErr_Clear();
	}
	// no ref added to m
	Py_XDECREF(func);
	Py_XDECREF(args);
	Py_XDECREF(result);
	PyGILState_Release(state);
	return rc;
}

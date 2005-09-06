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

#include <windows.h>
#include <stdio.h>
#include <olectl.h>

#include <assert.h>
#include "Python-dynload.h"
#include "MemoryModule.h"

// Function pointers we load from _ctypes.pyd
typedef int (__stdcall *__PROC__DllCanUnloadNow) (void);
typedef HRESULT (__stdcall *__PROC__DllGetClassObject) (REFCLSID, REFIID, LPVOID *);

CRITICAL_SECTION csInit; // protecting our init code

__PROC__DllCanUnloadNow Pyc_DllCanUnloadNow = NULL;
__PROC__DllGetClassObject Pyc_DllGetClassObject = NULL;

extern void init_memimporter(void);

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
HANDLE g_ctypes = 0;
HMODULE gInstance = 0;

extern int init_with_instance(HMODULE, char *);
extern void fini();
extern int run_script(void);

int load_ctypes(void)
{
	char dll_path[_MAX_PATH+_MAX_FNAME+1];

	// shouldn't do this twice
	assert(g_ctypes == NULL);
#ifdef _DEBUG
	strcpy(dll_path, "_ctypes_d.pyd");
#else
	strcpy(dll_path, "_ctypes.pyd");
#endif
	g_ctypes = MyGetModuleHandle(dll_path);
/*
	if (g_ctypes == NULL) {
		// not already loaded - try and load from the current dir
		char *temp;
		GetModuleFileNameA(gInstance, dll_path, sizeof(dll_path));
		temp = dll_path + strlen(dll_path);
		while (temp>dll_path && *temp != '\\')
			temp--;
		// and printf directly in the buffer.
		// temp points to '\\filename.ext'!
#ifdef _DEBUG
		g_ctypes = MyGetModuleHandle("_ctypes_d.pyd");
#else
		g_ctypes = MyGetModuleHandle("_ctypes.pyd");
#endif
		g_ctypes = LoadLibraryEx(dll_path, // points to name of executable module 
					 NULL, // HANDLE hFile, // reserved, must be NULL 
					 LOAD_WITH_ALTERED_SEARCH_PATH // DWORD dwFlags // entry-point execution flag 
			); 
	}
*/
	if (g_ctypes == NULL) {
		OutputDebugString("GetModuleHandle _ctypes?.pyd failed");
		// give up in disgust
		return -1;
	}

	Pyc_DllCanUnloadNow = (__PROC__DllCanUnloadNow)MyGetProcAddress(g_ctypes, "DllCanUnloadNow");
	Pyc_DllGetClassObject = (__PROC__DllGetClassObject)MyGetProcAddress(g_ctypes, "DllGetClassObject");
	return 0;
}

int check_init()
{
	if (!have_init) {
		EnterCriticalSection(&csInit);
		// Check the flag again - another thread may have beat us to it!
		if (!have_init) {
			PyObject *frozen;
			/* If Python had previously been initialized, we must use
			   PyGILState_Ensure normally.  If Python has not been initialized,
			   we must leave the thread state unlocked, so other threads can
			   call in.
			*/
			PyGILState_STATE restore_state = PyGILState_UNLOCKED;
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
			if (g_ctypes == NULL)
				load_ctypes();
			// Reset the thread-state, so any thread can call in
			PyGILState_Release(restore_state);
		}
		LeaveCriticalSection(&csInit);
	}
	return g_ctypes != NULL;
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

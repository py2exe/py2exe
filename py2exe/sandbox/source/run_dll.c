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
#include <Python.h> // XXX

// Function pointers we load from pythoncom
typedef int (__stdcall *__PROC__DllCanUnloadNow) (void);
typedef HRESULT (__stdcall *__PROC__DllGetClassObject) (REFCLSID, REFIID, LPVOID *);
typedef void (__cdecl *__PROC__PyCom_CoUninitialize) (void);

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

extern int init_with_instance(HMODULE);
extern void fini();
extern int run_script(void);

int load_pythoncom(void)
{
	char dll_path[_MAX_PATH+_MAX_FNAME+1];
	char *winver = "";
	char major = 'x', minor = 'y';
#ifdef _DEBUG
	char *suffix = "_d";
#else
	char *suffix = "";
#endif

	PyObject *ob_winver = PySys_GetObject("winver");
	if (PyString_Check(ob_winver))
		winver = PyString_AsString(ob_winver);
	// works until Python 10!
	if (winver && strlen(winver)>=3) {
		major = winver[0];
		minor = winver[2];
	}

	// shouldn't do this twice
	assert(gPythoncom == NULL);

	snprintf(dll_path, sizeof(dll_path), "pythoncom%c%c%s.dll", major, minor, suffix);
	gPythoncom = GetModuleHandle(dll_path);
	if (gPythoncom == NULL) {
		// not already loaded - try and load from the current dir
		char *temp;
		GetModuleFileNameA(gInstance, dll_path, sizeof(dll_path));
		temp = dll_path + strlen(dll_path);
		while (temp>dll_path && *temp != '\\')
			temp--;
		// and printf directly in the buffer.
		snprintf(temp, sizeof(dll_path)-strlen(temp),
			 "pythoncom%c%c%s.dll", major, minor, suffix);
		gPythoncom = LoadLibraryEx(dll_path, // points to name of executable module 
					   NULL, // HANDLE hFile, // reserved, must be NULL 
					   LOAD_WITH_ALTERED_SEARCH_PATH // DWORD dwFlags // entry-point execution flag 
			); 
	}
	Py_XDECREF(ob_winver);
	if (gPythoncom == NULL)
		// give up in disgust
		return -1;

	Pyc_DllCanUnloadNow = (__PROC__DllCanUnloadNow)GetProcAddress(gPythoncom, "DllCanUnloadNow");
	Pyc_DllGetClassObject = (__PROC__DllGetClassObject)GetProcAddress(gPythoncom, "DllGetClassObject");
	PyCom_CoUninitialize = (__PROC__PyCom_CoUninitialize)GetProcAddress(gPythoncom, "PyCom_CoUninitialize");
	return 0;
}

int check_init()
{
	if (!have_init) {
		PyObject *frozen;
		init_with_instance(gInstance);
		// a little DLL magic.  Set sys.frozen='dll'
		frozen = PyString_FromString("dll");
		if (frozen) {
			PySys_SetObject("frozen", frozen);
			Py_DECREF(frozen);
		}
		frozen = PyInt_FromLong((LONG)gInstance);
		if (frozen) {
			PySys_SetObject("frozendllhandle", frozen);
			Py_DECREF(frozen);
		}
		// Now run the generic script - this always returns in a DLL.
		run_script();
		have_init = TRUE;
	}
	if (gPythoncom == NULL)
		load_pythoncom();
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
	}
	else if ( dwReason == DLL_PROCESS_DETACH ) {
		gInstance = 0;
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
	check_init();
	rc = PyRun_SimpleString("DllRegisterServer()\n");
	if (rc != 0)
		PyErr_Print();
	return rc==0 ? 0 : SELFREG_E_CLASS;
}

STDAPI DllUnregisterServer()
{
	int rc=0;
	check_init();
	rc = PyRun_SimpleString("DllUnregisterServer()\n");
	if (rc != 0)
		PyErr_Print();
	return rc==0 ? 0 : SELFREG_E_CLASS;
}

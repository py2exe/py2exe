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
#include "httpext.h"
#include <httpfilt.h>
//#include "Python.h"
#include <stdio.h>
#include "Python-dynload.h"


typedef BOOL (__stdcall *__PROC__GetExtensionVersion)(HSE_VERSION_INFO  *pVer);
typedef BOOL (__stdcall *__PROC__HttpExtensionProc)(EXTENSION_CONTROL_BLOCK *pECB);
typedef BOOL (__stdcall *__PROC__TerminateExtension)(DWORD dwFlags);
typedef BOOL (__stdcall *__PROC__GetFilterVersion)(HTTP_FILTER_VERSION *pVer);
typedef DWORD (__stdcall *__PROC__HttpFilterProc)(HTTP_FILTER_CONTEXT *phfc, DWORD NotificationType, VOID *pvData);
typedef BOOL (__stdcall *__PROC__TerminateFilter)(DWORD status);
typedef void (__stdcall *__PROC__PyISAPISetOptions)(const char *modname, BOOL is_frozen);


CRITICAL_SECTION csInit; // protecting our init code
HMODULE gInstance = 0;
HMODULE hmodPyISAPI = 0;
BOOL have_init = FALSE;

__PROC__GetExtensionVersion pGetExtensionVersion = NULL;
__PROC__HttpExtensionProc pHttpExtensionProc = NULL;
__PROC__TerminateExtension pTerminateExtension = NULL;
__PROC__GetFilterVersion pGetFilterVersion = NULL;
__PROC__HttpFilterProc pHttpFilterProc = NULL;
__PROC__TerminateFilter pTerminateFilter = NULL;
__PROC__PyISAPISetOptions pPyISAPISetOptions = NULL;

extern int init_with_instance(HMODULE, char *);
extern BOOL _LoadPythonDLL(HMODULE);

extern void fini();
extern int run_script(void);
extern void init_memimporter(void);

void SystemError(int error, char *msg)
{
	char Buffer[1024];
	int n;
	HANDLE hEventSource;

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
	// Can't display messages in a service.  Write to the event log.
	// We have no message resources, so the message will be somewhat
	// ugly - but so long as the info is there, that's ok.
	hEventSource = RegisterEventSource(NULL, "ISAPI Filter or Extension");
	if (hEventSource) {
		TCHAR * inserts[] = {Buffer};
		ReportEvent(hEventSource, // handle of event source
		            EVENTLOG_ERROR_TYPE,  // event type
		            0,                    // event category
		            1,                 // event ID
		            NULL,                 // current user's SID
		            1,           // strings in lpszStrings
		            0,                    // no bytes of raw data
		            inserts,          // array of error strings
		            NULL);                // no raw data
		DeregisterEventSource(hEventSource);
	}
}

BOOL check_init()
{
	if (!have_init) {
		EnterCriticalSection(&csInit);
		// Check the flag again - another thread may have beat us to it!
		if (!have_init) {
			PyGILState_STATE restore_state = PyGILState_UNLOCKED;
			PyObject *frozen;
			char dll_path[1024];
			char *slash;
			// Find and load the pyisapi DLL.
			GetModuleFileName(gInstance, dll_path, sizeof(dll_path)/sizeof(dll_path[0]));
			slash = strrchr(dll_path, '\\');
			if (slash) {
				// insert an underscore.
				char *pos_move = dll_path + strlen(dll_path);
				while (pos_move > slash) {
					*(pos_move+1) = *pos_move;
					pos_move --;
				}
				*(slash+1) = '_';
				hmodPyISAPI = LoadLibrary(dll_path);
				if (hmodPyISAPI) {
					pGetExtensionVersion = (__PROC__GetExtensionVersion)GetProcAddress(hmodPyISAPI, "GetExtensionVersion");
					pHttpExtensionProc = (__PROC__HttpExtensionProc)GetProcAddress(hmodPyISAPI, "HttpExtensionProc");
					pTerminateExtension = (__PROC__TerminateExtension)GetProcAddress(hmodPyISAPI, "TerminateExtension");
					pGetFilterVersion  = (__PROC__GetFilterVersion)GetProcAddress(hmodPyISAPI, "GetFilterVersion");
					pHttpFilterProc = (__PROC__HttpFilterProc)GetProcAddress(hmodPyISAPI, "HttpFilterProc");
					pTerminateFilter = (__PROC__TerminateFilter)GetProcAddress(hmodPyISAPI, "TerminateFilter");
					pPyISAPISetOptions = (__PROC__PyISAPISetOptions)GetProcAddress(hmodPyISAPI, "PyISAPISetOptions");
				}
			}

			// We must ensure Python is loaded, and therefore the
			// function pointers are non-NULL, or this check is
			// pointless
			if (!_LoadPythonDLL(gInstance))
				return FALSE;

			if (Py_IsInitialized && Py_IsInitialized())
				restore_state = PyGILState_Ensure();
			// a little DLL magic.  Set sys.frozen='dll'
			if (init_with_instance(gInstance, "dll") != 0)
				return FALSE;
			init_memimporter();
			frozen = PyInt_FromLong((LONG)gInstance);
			if (frozen) {
				PySys_SetObject("frozendllhandle", frozen);
				Py_DECREF(frozen);
			}
			// Now run the generic script - this always returns in a DLL.
			run_script();
			// Let the ISAPI extension know about the frozen environment.
			// (the ISAPI boot code currently has no way of talking directly
			// to the pyISAPI dll, so we fetch it directly from the py2exe
			// 'variable' which is already in module '__main__'.
			if (pPyISAPISetOptions) {
				PyObject *main = PyImport_ImportModule("__main__");
				if (main) {
					PyObject *name = PyObject_GetAttrString(main, "isapi_module_name");
					char *str;
					if (name && (str = PyString_AsString(name)))
						(*pPyISAPISetOptions)(str, TRUE);
					else
						PyErr_Clear(); // In case PyString_AsString fails
					Py_XDECREF(name);
				}
				Py_DECREF(main);
			}
			have_init = TRUE;
			PyGILState_Release(restore_state);
		}
		LeaveCriticalSection(&csInit);
	}
	return TRUE;
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
		if (hmodPyISAPI)
			FreeLibrary(hmodPyISAPI);
		DeleteCriticalSection(&csInit);
	}
	return TRUE; 
}

BOOL WINAPI GetExtensionVersion(HSE_VERSION_INFO *pVer)
{
	if (!check_init() || !pGetExtensionVersion) return FALSE;
	return (*pGetExtensionVersion)(pVer);
}
DWORD WINAPI HttpExtensionProc(EXTENSION_CONTROL_BLOCK *pECB)
{
	if (!check_init() || !pHttpExtensionProc) return FALSE;
	return (*pHttpExtensionProc)(pECB);
}
BOOL WINAPI TerminateExtension(DWORD dwFlags)
{
	if (!check_init() || !pTerminateExtension) return FALSE;
	return (*pTerminateExtension)(dwFlags);
}

BOOL WINAPI GetFilterVersion(HTTP_FILTER_VERSION *pVer)
{
	if (!check_init() || !pGetFilterVersion) return FALSE;
	return (*pGetFilterVersion)(pVer);
}

DWORD WINAPI HttpFilterProc(HTTP_FILTER_CONTEXT *phfc, DWORD NotificationType, VOID *pvData)
{
	if (!check_init() || !pHttpFilterProc) return FALSE;
	return (*pHttpFilterProc)(phfc, NotificationType, pvData);
}

BOOL WINAPI TerminateFilter(DWORD status)
{
	if (!check_init() || !pTerminateFilter) return FALSE;
	return (*pTerminateFilter)(status);
}

/*
 *	   Copyright (c) 2000, 2001 Thomas Heller
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

/*
 * Create a Windows NT service
 *
 * $Id$
 *
 * $Log$
 * Revision 1.2  2002/01/29 09:29:39  theller
 * version 0.3.0
 *
 * Revision 1.1  2002/01/16 14:41:59  theller
 * Works, but still needs lots of improvements.
 *
 *
 */

#include <windows.h>
#include <stdio.h>
#include "Python.h"

/* Copied from PythonService.cpp: resource ID in the EXE of the service class */

#define RESOURCE_SERVICE_NAME 1016 /* this is the class implementing the service */

/* This one and the next two strings resources contain the service name, the
 * display name, and the service dependencies separated by '|' characters.
 */

extern void PyWinFreeze_ExeInit();
extern int PyInitFrozenExtensions();

static BOOL GetServiceNames(char **exe_name, char **svc_name,
			    char **svc_displayname, char **svc_deps)
{
    static char svc_name_buf[256];
    static char svc_displayname_buf[256];
    static char exename_buf[MAX_PATH];
    static char svc_deps_buf[512];
    
    GetModuleFileName(NULL, exename_buf, sizeof(exename_buf));
    if (0 == LoadString(GetModuleHandle(NULL), RESOURCE_SERVICE_NAME+1,
			svc_name_buf, sizeof(svc_name_buf))) {
	fprintf(stderr, "Service Name not found\n");
	return FALSE;
    }
    if (0 == LoadString(GetModuleHandle(NULL), RESOURCE_SERVICE_NAME+2,
			svc_displayname_buf, sizeof(svc_displayname_buf))) {
	strcpy(svc_displayname_buf, svc_name_buf);
    }
    /* The svc_deps code was contributed by Matthew King. */
    if (0 == LoadString(GetModuleHandle(NULL), RESOURCE_SERVICE_NAME+3,
			svc_deps_buf, sizeof(svc_deps_buf)-1)) {
	strcpy(svc_deps_buf, "");
    } else {
	/* turn into a double null-terminated array of null-separated names
	 * rely on staric buf bening initialized wuth nulls to give double
	 * null on the end */
	char *p;
	for (p=svc_deps_buf; *p; p++) {
	    if (*p == '|')
		*p = '\0';
	}
    }
    if (svc_name)
	*svc_name = svc_name_buf;
    if (svc_displayname)
	*svc_displayname = svc_displayname_buf;
    if (exe_name)
	*exe_name = exename_buf;
    if (svc_deps)
	*svc_deps = svc_deps_buf;
    return TRUE;
}

BOOL InstallService(void)
{
    char *exe_name, *svc_name, *svc_displayname, *svc_deps;
    SC_HANDLE hmgr, hservice;

    if (!GetServiceNames(&exe_name, &svc_name, &svc_displayname, &svc_deps)) {
	fprintf(stderr, "Service Name not found\n");
	return FALSE;
    }

    hmgr = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
    if (hmgr == NULL) {
	fprintf(stderr, "Could not open service manager, error code %d\n", GetLastError());
	return FALSE; // XXX ReportAPIError
    }

    hservice = CreateService(hmgr,
			     svc_name, // Name of service
			     svc_displayname, // displayname
			     SERVICE_ALL_ACCESS,        // desired access 
			     SERVICE_WIN32_OWN_PROCESS, // service type 
			     SERVICE_DEMAND_START,      // start type 
			     SERVICE_ERROR_NORMAL,      // error control type 
			     exe_name,		        // service's binary 
			     NULL,                      // no load ordering group 
			     NULL,                      // no tag identifier 
			     svc_deps,                  // no dependencies 
			     NULL,                      // LocalSystem account 
			     NULL);                     // no password 

    if (hservice)
	fprintf(stderr, "Service '%s' (%s) installed\n", svc_name, svc_displayname);
    else {
	fprintf(stderr, "Service '%s' could not be installed, error code %d\n",
		svc_name, GetLastError());
	CloseServiceHandle(hservice);
    }
    CloseServiceHandle(hmgr);
    return hservice ? TRUE : FALSE;
}

BOOL RemoveService(void)
{
    char *svc_name, *svc_displayname;
    SC_HANDLE hmgr, hservice;
    BOOL result;

    if (!GetServiceNames(NULL, &svc_name, &svc_displayname, NULL)) {
	fprintf(stderr, "Service Name not found\n");
	return FALSE;
    }

    hmgr = OpenSCManager(NULL, NULL, SC_MANAGER_ALL_ACCESS);
    if (hmgr == NULL) {
	fprintf(stderr, "Could not open service manager, error code %d\n", GetLastError());
	return FALSE; // XXX ReportAPIError
    }
    hservice = OpenService(hmgr,
			   svc_name,
			   SERVICE_ALL_ACCESS);
    if (!hservice) {
	fprintf(stderr, "Could not open service '%s', error code %d\n", svc_name, GetLastError());
	return FALSE;
    }

    result = DeleteService(hservice);
    if (result) {
	CloseServiceHandle(hservice);
	fprintf(stderr, "Service '%s' removed\n", svc_name);
    } else {
	fprintf(stderr, "Service '%s' could not be removed, error code %d\n", GetLastError());
    }
    CloseServiceHandle(hmgr);
    return result;
}

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

extern int init(void);
extern int start(int argc, char **argv);

extern int PythonService_main(int argc, char **argv);

void PyWinFreeze_ExeInit()
{
}

int PyInitFrozenExtensions()
{
    return 0;
}

int main (int argc, char **argv)
{
    int result;
    result = init();
    if (result)
	return result;
    return PythonService_main(argc, argv);
}

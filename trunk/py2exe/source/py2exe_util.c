/*
 *	   Copyright (c) 2000, 2001, 2002, 2003 Thomas Heller
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

#include "Python.h"
#include <windows.h>
#include <imagehlp.h>

static char module_doc[] =
"Utility functions for the py2exe package";

HANDLE (__stdcall *pfn_BeginUpdateResource)(LPCWSTR, BOOL);
BOOL (__stdcall* pfn_EndUpdateResource)(HANDLE, BOOL);
BOOL (__stdcall* pfn_UpdateResource)(HANDLE, LPCWSTR, LPCWSTR, WORD, LPVOID, DWORD);
HANDLE (__stdcall* pfn_CreateFileW)(LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);

static PyObject *SystemError(int code, char *msg)
{
    LPVOID lpMsgBuf;
    char Buffer[4096];
    FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER
		  | FORMAT_MESSAGE_FROM_SYSTEM,
		  NULL,
		  code,
		  MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
		  (LPSTR) &lpMsgBuf,
		  0,
		  NULL);
    sprintf(Buffer, "%s: %s", msg, lpMsgBuf);
    LocalFree (lpMsgBuf);
    PyErr_SetString(PyExc_RuntimeError, Buffer);
    return NULL;
}

Py_UNICODE *PyObject_AsRESOURCEID(PyObject *py_res_type)
{
    if (PyInt_Check(py_res_type))
        return (Py_UNICODE *)MAKEINTRESOURCE(PyInt_AsLong(py_res_type));
    if (PyUnicode_Check(py_res_type))
	    return PyUnicode_AS_UNICODE(py_res_type);
    PyErr_Format(PyExc_ValueError,
        "resource argument must be int or unicode (not '%s')",
        py_res_type->ob_type->tp_name);
    return NULL;
}

/*
 * Ref for the icon code, from MSDN:
 *   Icons in Win32
 *   John Hornick 
 *   Microsoft Corporation
 *     Created: September 29, 1995
 */

#pragma pack(2)

/* Structure of .ico files */

typedef struct {
    BYTE bWidth;
    BYTE bHeight;
    BYTE bColorCount;
    BYTE bReserved;
    WORD wPlanes;
    WORD wBitCount;
    DWORD dwBytesInRes;
    DWORD dwImageOffset;
} ICONDIRENTRY;

typedef struct {
    WORD idReserved; /* Must be 0 */
    WORD idType; /* Should check that this is 1 for icons */
    WORD idCount; /* Number os ICONDIRENTRYs to follow */
    ICONDIRENTRY idEntries[0];
} ICONDIRHEADER;

/* Format of RT_GROUP_ICON resources */

typedef struct {
    BYTE bWidth;
    BYTE bHeight;
    BYTE bColorCount;
    BYTE bReserved;
    WORD wPlanes;
    WORD wBitCount;
    DWORD dwBytesInRes;
    WORD nID;
} GRPICONDIRENTRY;

typedef struct {
    WORD idReserved;
    WORD idType;
    WORD idCount;
    GRPICONDIRENTRY idEntries[0];
} GRPICONDIRHEADER;

#pragma pack()

/*
 * Map a file into memory for reading.
 *
 * Pointer returned must be freed with UnmapViewOfFile().
 */
static char *MapExistingFile (Py_UNICODE *pathname, DWORD *psize)
{
    HANDLE hFile, hFileMapping;
    DWORD nSizeLow, nSizeHigh;
    char *data;

    if (pfn_CreateFileW == NULL) {
	SetLastError(1); /* Incorrect function */
	return NULL;
    }
    hFile = pfn_CreateFileW(pathname,
			    GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING,
			    FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile == INVALID_HANDLE_VALUE)
	return NULL;
    nSizeLow = GetFileSize(hFile, &nSizeHigh);
    hFileMapping = CreateFileMapping(hFile,
				     NULL, PAGE_READONLY, 0, 0, NULL);
    CloseHandle (hFile);

    if (hFileMapping == INVALID_HANDLE_VALUE)
	return NULL;
    
    data = MapViewOfFile(hFileMapping,
	FILE_MAP_READ, 0, 0, 0);

    CloseHandle(hFileMapping);
    *psize = nSizeLow;
    return data;
}

/*
 * Create a GRPICONDIRHEADER from an ICONDIRHEADER.
 *
 * Returns malloc()'d memory.
 */
static GRPICONDIRHEADER *CreateGrpIconDirHeader(ICONDIRHEADER *pidh, int icoid)
{
    GRPICONDIRHEADER *pgidh;
    size_t size;
    int i;

    size = sizeof(GRPICONDIRHEADER) + sizeof(GRPICONDIRENTRY) * pidh->idCount;
    pgidh = (GRPICONDIRHEADER *)malloc(size);
    pgidh->idReserved = pidh->idReserved;
    pgidh->idType = pidh->idType;
    pgidh->idCount = pidh->idCount;

    for (i = 0; i < pidh->idCount; ++i) {
	pgidh->idEntries[i].bWidth = pidh->idEntries[i].bWidth;
	pgidh->idEntries[i].bHeight = pidh->idEntries[i].bHeight;
	pgidh->idEntries[i].bColorCount = pidh->idEntries[i].bColorCount;
	pgidh->idEntries[i].bReserved = pidh->idEntries[i].bReserved;
	pgidh->idEntries[i].wPlanes = pidh->idEntries[i].wPlanes;
	pgidh->idEntries[i].wBitCount = pidh->idEntries[i].wBitCount;
	pgidh->idEntries[i].dwBytesInRes = pidh->idEntries[i].dwBytesInRes;
	pgidh->idEntries[i].nID = icoid + i ;
    }
    return pgidh;
}

static PyObject* do_add_icon(Py_UNICODE *exename, Py_UNICODE *iconame, int icoid, BOOL bDelete)
{
    static rt_icon_id = 0;

    /* from the .ico file */
    ICONDIRHEADER *pidh;
    WORD idh_size;
    /* for the resources */
    GRPICONDIRHEADER *pgidh = NULL;
    WORD gidh_size;
    HANDLE hUpdate = NULL;
    int i;
    char *icodata;
    DWORD icosize;
    icodata = MapExistingFile(iconame, &icosize);
    if (!icodata) {
        return SystemError(GetLastError(), "MapExistingFile");
    }
    
    pidh = (ICONDIRHEADER *)icodata;
    idh_size = sizeof(ICONDIRHEADER) + sizeof(ICONDIRENTRY) * pidh->idCount;

    pgidh = CreateGrpIconDirHeader(pidh, icoid);
    gidh_size = sizeof(GRPICONDIRHEADER) + sizeof(GRPICONDIRENTRY) * pgidh->idCount;

    if (pfn_BeginUpdateResource == NULL
	|| pfn_UpdateResource == NULL
	|| pfn_EndUpdateResource == NULL) {
	PyErr_SetString(PyExc_RuntimeError,
			"this function requires unicows.dll in the Python directory on Win 95/98/Me");
	return NULL;
    }

    hUpdate = pfn_BeginUpdateResource(exename, bDelete);
    if (!hUpdate) {
	SystemError(GetLastError(), "BeginUpdateResource");
	goto failed;
    }
    
    /* Each RT_ICON resource in an image file (containing the icon for one
       specific resolution and number of colors) must have a unique id, and
       the id must be in the GRPICONDIRHEADER's nID member.

       So, we use a *static* variable rt_icon_id which is incremented for each
       RT_ICON resource and written into the GRPICONDIRHEADER's nID member.

       XXX Do we need a way to reset the rt_icon_id variable to zero?  If we
       are building a lot of images in one setup script? 
    */
    for (i = 0; i < pidh->idCount; ++i) {
	    pgidh->idEntries[i].nID = rt_icon_id++;
    }
    if (!pfn_UpdateResource(hUpdate,
			    (Py_UNICODE *)MAKEINTRESOURCE(RT_GROUP_ICON),
			    (Py_UNICODE *)MAKEINTRESOURCE(icoid),
			    MAKELANGID(LANG_NEUTRAL, SUBLANG_NEUTRAL),
			    pgidh,
			    gidh_size)) {
	SystemError(GetLastError(), "UpdateResource");
	goto failed;
    }
    for (i = 0; i < pidh->idCount; ++i) {
        char *cp = &icodata[pidh->idEntries[i].dwImageOffset];
        int cBytes = pidh->idEntries[i].dwBytesInRes;
        if (!pfn_UpdateResource(hUpdate,
				(Py_UNICODE *)MAKEINTRESOURCE(RT_ICON),
				(Py_UNICODE *)MAKEINTRESOURCE(pgidh->idEntries[i].nID),
				MAKELANGID(LANG_NEUTRAL, SUBLANG_NEUTRAL),
				cp,
				cBytes)) {
            SystemError(GetLastError(), "UpdateResource");
            goto failed;
        }
    }

    free(pgidh);
    UnmapViewOfFile(icodata);

    if (!pfn_EndUpdateResource(hUpdate, FALSE))
        return SystemError(GetLastError(), "EndUpdateResource");
    Py_INCREF(Py_None);
    return Py_None;

  failed:
    if (pgidh)
        free(pgidh);
    if (hUpdate)
        pfn_EndUpdateResource(hUpdate, TRUE);
    if (icodata)
        UnmapViewOfFile(icodata);
    return NULL;
}

static PyObject *update_icon(PyObject *self, PyObject *args)
{
    Py_UNICODE *exename;
    Py_UNICODE *iconame;
    BOOL bDelete = 0;

    if (!PyArg_ParseTuple(args, "uu|i", &exename, &iconame, &bDelete))
        return NULL;
    return do_add_icon(exename, iconame, 1, bDelete);
}

static PyObject *add_icon(PyObject *self, PyObject *args)
{
    Py_UNICODE *exename;
    Py_UNICODE *iconame;
    int resid;
    BOOL bDelete = 0;

    if (!PyArg_ParseTuple(args, "uui|i", &exename, &iconame, &resid, &bDelete))
        return NULL;

    return do_add_icon(exename, iconame, resid, bDelete);
}

static PyObject *add_resource(PyObject *self, PyObject *args)
{
    Py_UNICODE *exename;
    HANDLE hUpdate = NULL;
    BOOL bDelete = 0;
    char *res_data;
    int res_size;
    PyObject *py_res_type, *py_res_id;
    Py_UNICODE *res_type;
    Py_UNICODE *res_id;

    if (!PyArg_ParseTuple(args, "us#OO|i",
			  &exename, &res_data, &res_size,
			  &py_res_type, &py_res_id, &bDelete))
	return NULL;

    if (pfn_BeginUpdateResource == NULL
	|| pfn_UpdateResource == NULL
	|| pfn_EndUpdateResource == NULL) {
	PyErr_SetString(PyExc_RuntimeError,
			"this function requires unicows.dll in the Python directory on Win 95/98/Me");
	return NULL;
    }

    res_type = PyObject_AsRESOURCEID(py_res_type);
    if (res_type==NULL)
        return NULL;

    res_id = PyObject_AsRESOURCEID(py_res_id);
    if (res_id==NULL)
        return NULL;

    hUpdate = pfn_BeginUpdateResource(exename, bDelete);
    if (!hUpdate) {
	SystemError(GetLastError(), "BeginUpdateResource");
	goto failed;
    }

    if (!pfn_UpdateResource(hUpdate,
			res_type,
			res_id,
			MAKELANGID(LANG_NEUTRAL, SUBLANG_NEUTRAL),
			res_data,
			res_size)) {
	SystemError(GetLastError(), "UpdateResource");
	goto failed;
    }

    if (!pfn_EndUpdateResource(hUpdate, FALSE))
	return SystemError(GetLastError(), "EndUpdateResource");
    Py_INCREF(Py_None);
    return Py_None;

  failed:
    if (hUpdate)
	pfn_EndUpdateResource(hUpdate, TRUE);
    return NULL;
}

/***********************************************************************************
 *
 * Dependency tracker
 *
 */

static char* searchpath;

static PyObject *py_result;

/* Exception */
static PyObject *BindError;


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
	break;

    case BindImportProcedure:
	if (0 == strcmp((LPSTR)Parameter, "PyImport_ImportModule")) {
	    PyDict_SetItemString(py_result, ImageName, PyInt_FromLong(1));
	}
	break;

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
	    PyDict_SetItemString(py_result, fname, PyInt_FromLong(0));
	else
	    PyDict_SetItemString(py_result, DllName, PyInt_FromLong(0));
	break;
    }
    return TRUE;
}

static PyObject *depends(PyObject *self, PyObject *args)
{
    char *imagename;
    PyObject *pdict;
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
    pBindImageEx = (BOOL(__stdcall *)(DWORD, LPSTR, LPSTR, LPSTR, PIMAGEHLP_STATUS_ROUTINE))
	GetProcAddress(hLib, "BindImageEx");
    if (!pBindImageEx) {
	PyErr_SetString(PyExc_SystemError,
			"imagehlp.dll does not export BindImageEx function");
	FreeLibrary(hLib);
	return NULL;
    }

    py_result = PyDict_New();
    if (!pBindImageEx(BIND_NO_BOUND_IMPORTS | BIND_NO_UPDATE | BIND_ALL_IMAGES,
		     imagename,
		     searchpath,
		     NULL,
		     StatusRoutine)) {
	FreeLibrary(hLib);
	Py_DECREF(py_result);
	PyErr_SetExcFromWindowsErrWithFilename(BindError, GetLastError(), imagename);
	return NULL;
    }
    FreeLibrary(hLib);
    if (PyErr_Occurred()) {
	Py_DECREF(py_result);
	return NULL;
    }
    pdict = py_result;
    py_result = NULL;
    return (PyObject *)pdict;
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
    { "add_resource", add_resource, METH_VARARGS,
      "add_resource(exe, res_data, res_size, res_type, res_id [, delete=0]) - add resource to an exe file\n"},
    { "add_icon", add_icon, METH_VARARGS,
      "add_icon(exe, ico, ico_id[, delete=0]) - add icon to an exe file\n"
      "If the delete flag is 1, delete all existing resources", },
    { "update_icon", update_icon, METH_VARARGS,
      "update_icon(exe, ico[, delete=0]) - add icon to an exe file\n"
      "If the delete flag is 1, delete all existing resources", },
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
    PyObject *m, *d;
    HMODULE hmod = NULL;

    if (GetVersion() & 0x80000000)
	/* Win 95, 98, Me */
	/* We don't check *here* if this fails. We check later! */
	hmod = LoadLibrary("unicows.dll");
    else
	/* Win NT, 2000, XP */
	hmod = LoadLibrary("kernel32.dll");

    pfn_BeginUpdateResource = (HANDLE (__stdcall *)(LPCWSTR, BOOL))
	GetProcAddress(hmod, "BeginUpdateResourceW");
    pfn_EndUpdateResource = (BOOL (__stdcall*)(HANDLE, BOOL))
	GetProcAddress(hmod, "EndUpdateResourceW");
    pfn_UpdateResource = (BOOL (__stdcall*)(HANDLE, LPCWSTR, LPCWSTR, WORD, LPVOID, DWORD))
	GetProcAddress(hmod, "UpdateResourceW");
    pfn_CreateFileW = (HANDLE (__stdcall*)(LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES,
					   DWORD, DWORD, HANDLE))
	GetProcAddress(hmod, "CreateFileW");
	
    
    m = Py_InitModule3("py2exe_util", methods, module_doc);
    if (m) {
	d = PyModule_GetDict(m);
	
	BindError = PyErr_NewException("py2exe_util.bind_error", NULL, NULL);
	if (BindError)
	    PyDict_SetItemString(d, "bind_error", BindError);
    }
}

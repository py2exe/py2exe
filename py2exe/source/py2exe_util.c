#include "Python.h"
#include <windows.h>
#include <imagehlp.h>

static char module_doc[] =
"Utility functions for the py2exe package";

static char *FormatError(DWORD code)
{
    LPVOID lpMsgBuf;
    FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER
		  | FORMAT_MESSAGE_FROM_SYSTEM,
		  NULL,
		  code,
		  MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
		  (LPSTR) &lpMsgBuf,
		  0,
		  NULL);
    return (char *)lpMsgBuf;
}

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
static char *MapExistingFile (char *pathname, DWORD *psize)
{
    HANDLE hFile, hFileMapping;
    DWORD nSizeLow, nSizeHigh;
    char *data;

    hFile = CreateFile (pathname,
	GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING,
	FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile == INVALID_HANDLE_VALUE)
	return NULL;
    nSizeLow = GetFileSize (hFile, &nSizeHigh);
    hFileMapping = CreateFileMapping (hFile,
	NULL, PAGE_READONLY, 0, 0, NULL);
    CloseHandle (hFile);

    if (hFileMapping == INVALID_HANDLE_VALUE)
	return NULL;
    
    data = MapViewOfFile (hFileMapping,
	FILE_MAP_READ, 0, 0, 0);

    CloseHandle (hFileMapping);
    *psize = nSizeLow;
    return data;
}

/*
 * Create a GRPICONDIRHEADER from an ICONDIRHEADER.
 *
 * Returns malloc()'d memory.
 */
static GRPICONDIRHEADER *CreateGrpIconDirHeader(ICONDIRHEADER *pidh)
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
	pgidh->idEntries[i].nID = i + 1;
    }
    return pgidh;
}

static PyObject *update_icon(PyObject *self, PyObject *args)
{
    char *exename;
    char *iconame;
    HANDLE hUpdate = NULL;
    int i;
    BOOL bDelete = 0;

    char *icodata;
    DWORD icosize;

    /* from the .ico file */
    ICONDIRHEADER *pidh;
    WORD idh_size;
    
    /* for the resources */
    GRPICONDIRHEADER *pgidh = NULL;
    WORD gidh_size;
    
    if (!PyArg_ParseTuple(args, "ss|i", &exename, &iconame, &bDelete))
	return NULL;

    icodata = MapExistingFile(iconame, &icosize);
    if (!icodata) {
	return SystemError(GetLastError(), "MapExistingFile");
    }
    
    pidh = (ICONDIRHEADER *)icodata;
    idh_size = sizeof(ICONDIRHEADER) + sizeof(ICONDIRENTRY) * pidh->idCount;

    pgidh = CreateGrpIconDirHeader(pidh);
    gidh_size = sizeof(GRPICONDIRHEADER) + sizeof(GRPICONDIRENTRY) * pgidh->idCount;

    hUpdate = BeginUpdateResource(exename, bDelete);
    if (!hUpdate) {
	SystemError(GetLastError(), "BeginUpdateResource");
	goto failed;
    }

    if (!UpdateResource(hUpdate,
			MAKEINTRESOURCE(RT_GROUP_ICON),
			MAKEINTRESOURCE(1),
			MAKELANGID(LANG_NEUTRAL, SUBLANG_NEUTRAL),
			pgidh,
			gidh_size)) {
	SystemError(GetLastError(), "UpdateResource");
	goto failed;
    }

    for (i = 0; i < pidh->idCount; ++i) {
	char *cp = &icodata[pidh->idEntries[i].dwImageOffset];
	int cBytes = pidh->idEntries[i].dwBytesInRes;

	if (!UpdateResource(hUpdate,
			    MAKEINTRESOURCE(RT_ICON),
			    MAKEINTRESOURCE(i+1),
			    MAKELANGID(LANG_NEUTRAL, SUBLANG_NEUTRAL),
			    cp,
			    cBytes)) {
	    SystemError(GetLastError(), "UpdateResource");
	    goto failed;
	}
    }

    free(pgidh);
    UnmapViewOfFile(icodata);

    if (!EndUpdateResource(hUpdate, FALSE))
	return SystemError(GetLastError(), "EndUpdateResource");
    Py_INCREF(Py_None);
    return Py_None;

  failed:
    if (pgidh)
	free(pgidh);
    if (hUpdate)
	EndUpdateResource(hUpdate, TRUE);
    if (icodata)
	UnmapViewOfFile(icodata);
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
    pBindImageEx = (FARPROC)GetProcAddress(hLib, "BindImageEx");
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
	PyErr_SetString(BindError, imagename);
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

    m = Py_InitModule3("py2exe_util", methods, module_doc);
    if (m) {
	d = PyModule_GetDict(m);

	BindError = PyErr_NewException("py2exe_util.bind_error", NULL, NULL);
	if (BindError)
	    PyDict_SetItemString(d, "bind_error", BindError);
    }
}

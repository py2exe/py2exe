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
 * $Id$
 *
 */

/*
#include <Python.h>
#include <marshal.h>
#include <compile.h>
#include <eval.h>
*/
#include "Python-dynload.h"
#include <stdio.h>
#include <windows.h>
#include "MemoryModule.h"

#if defined(MS_WINDOWS) || defined(__CYGWIN__)
#include <fcntl.h>
#endif

struct scriptinfo {
	int tag;
	int optimize;
	int unbuffered;
	int data_bytes;

	char zippath[0];
};

extern void SystemError(int error, char *msg);
int run_script(void);
void fini(void);
char *pScript;
char *pZipBaseName;
int numScriptBytes;
char modulename[_MAX_PATH + _MAX_FNAME + _MAX_EXT]; // from GetModuleName()
char dirname[_MAX_PATH]; // directory part of GetModuleName()
char libdirname[_MAX_PATH]; // library directory - probably same as above.
char libfilename[_MAX_PATH + _MAX_FNAME + _MAX_EXT]; // library filename
struct scriptinfo *p_script_info;


/*
static int dprintf(char *fmt, ...)
{
	char Buffer[4096];
	va_list marker;
	int result;

	va_start(marker, fmt);
	result = vsprintf(Buffer, fmt, marker);
	OutputDebugString(Buffer);
	return result;
}
*/

BOOL _LocateScript(HMODULE hmod)
{
	HRSRC hrsrc = FindResource(hmod, MAKEINTRESOURCE(1), "PYTHONSCRIPT");
	HGLOBAL hgbl;
	char *cp;

	// get module filename
	if (!GetModuleFileName(hmod, modulename, sizeof(modulename))) {
		SystemError(GetLastError(), "Retrieving module name");
		return FALSE;
	}
	// get directory of modulename
	strcpy(dirname, modulename);
	cp = strrchr(dirname, '\\');
	*cp = '\0';

	// load the script resource
	if (!hrsrc) {
		SystemError(GetLastError(), "Could not locate script resource:");
		return FALSE;
	}
	hgbl = LoadResource(hmod, hrsrc);
	if (!hgbl) {
		SystemError(GetLastError(), "Could not load script resource:");
		return FALSE;
	}
	p_script_info = (struct scriptinfo *)pScript = LockResource(hgbl);
	if (!pScript)  {
		SystemError(GetLastError(), "Could not lock script resource:");
		return FALSE;
	}
	// validate script resource
	numScriptBytes = p_script_info->data_bytes;
	pScript += sizeof(struct scriptinfo);
	if (p_script_info->tag != 0x78563412) {
		SystemError (0, "Bug: Invalid script resource");
		return FALSE;
	}
	// let pScript point to the start of the python script resource
	pScript += strlen(p_script_info->zippath) + 1;

	// get full pathname of the 'library.zip' file
	snprintf(libfilename, sizeof(libfilename),
		 "%s\\%s", dirname, p_script_info->zippath);
	return TRUE; // success
}

static char *MapExistingFile(char *pathname, DWORD *psize)
{
	HANDLE hFile, hFileMapping;
	DWORD nSizeLow, nSizeHigh;
	char *data;

	hFile = CreateFile(pathname,
			    GENERIC_READ, FILE_SHARE_READ, NULL,
			    OPEN_EXISTING,
			    FILE_ATTRIBUTE_NORMAL, NULL);
	if (hFile == INVALID_HANDLE_VALUE)
		return NULL;
	nSizeLow = GetFileSize(hFile, &nSizeHigh);
	hFileMapping = CreateFileMapping(hFile,
					 NULL, PAGE_READONLY, 0, 0, NULL);
	CloseHandle(hFile);

	if (hFileMapping == INVALID_HANDLE_VALUE)
		return NULL;

	data = MapViewOfFile(hFileMapping,
			     FILE_MAP_READ, 0, 0, 0);

	CloseHandle(hFileMapping);
	if (psize)
		*psize = nSizeLow;
	return data;
}

BOOL _LoadPythonDLL(HMODULE hmod)
{
	HRSRC hrsrc;
	char *pBaseAddress;
	int size;

	// Try to locate pythonxy.dll as resource in the exe
	hrsrc = FindResource(hmod, MAKEINTRESOURCE(1), PYTHONDLL);
	if (hrsrc) {
		HGLOBAL hgbl = LoadResource(hmod, hrsrc);
		if (!_load_python(PYTHONDLL, LockResource(hgbl))) {
			SystemError(GetLastError(), "Could not load python dll");
			return FALSE;
		}
//		dprintf("Loaded pythondll as RESOURCE\n");
		return TRUE;
	}

	// try to load pythonxy.dll as bytes at the start of the zipfile
	pBaseAddress = MapExistingFile(libfilename, &size);
	if (pBaseAddress) {
		int res = 0;
		if (0 == strncmp(pBaseAddress, "<pythondll>", 11))
			res = _load_python(PYTHONDLL, pBaseAddress + 11 + sizeof(int));
		UnmapViewOfFile(pBaseAddress);
		if (res) {
//			dprintf("Loaded pythondll as <pythondll> from %s\n", libfilename);
			return TRUE;
		}
	}

	// try to load pythonxy.dll from the file system
	{
		char buffer[_MAX_PATH + _MAX_FNAME + _MAX_EXT];
		snprintf(buffer, sizeof(buffer), "%s\\%s", dirname, PYTHONDLL);

		if (!_load_python(buffer, NULL)) {
			SystemError(GetLastError(), "LoadLibrary(pythondll) failed");
			return FALSE;
		}
//		dprintf("Loaded pythondll from file %s\n", buffer);
	}
	return TRUE;
}

void _Import_Zlib(char *pdata)
{
	HMODULE hlib;
	hlib = MemoryLoadLibrary("zlib.pyd", pdata);
	if (hlib) {
		void (*proc)(void);
		proc = (void(*)(void))MemoryGetProcAddress(hlib, "initzlib");
		if (proc)
			proc();
	}
}

void _TryLoadZlib(HMODULE hmod)
{
	char *pBaseAddress;
	char *pdata;
	HRSRC hrsrc;

	// Try to locate pythonxy.dll as resource in the exe
	hrsrc = FindResource(hmod, MAKEINTRESOURCE(1), "ZLIB.PYD");
	if (hrsrc) {
		HGLOBAL hglb = LoadResource(hmod, hrsrc);
		if (hglb) {
			_Import_Zlib(LockResource(hglb));
		}
		return;
	}

	// try to load zlib.pyd as bytes at the start of the zipfile
	pdata = pBaseAddress = MapExistingFile(libfilename, NULL);
	if (pBaseAddress) {
		if (0 == strncmp(pBaseAddress, "<pythondll>", 11)) {
			pdata += 11;
			pdata += *(int *)pdata + sizeof(int);
		}
		if (0 == strncmp(pdata, "<zlib.pyd>", 10)) {
			pdata += 10 + sizeof(int);
			_Import_Zlib(pdata);
		}
		UnmapViewOfFile(pBaseAddress);
	}
}

static void calc_path()
{
	/* If the zip path has any path component, then build our Python
	   home directory from that.
	*/
	char *fname;
	int lib_dir_len;
	pZipBaseName = pScript - 1;
	/* let pZipBaseName point to the basename of the zippath */
	while (pZipBaseName > p_script_info->zippath && \
	       *(pZipBaseName-1) != '\\')
		pZipBaseName--;
	/* dirname is the directory of the executable */
	strcpy(libdirname, dirname);
	/* length of lib director name */
	lib_dir_len = pZipBaseName-p_script_info->zippath; /* incl. tail slash */
	if (lib_dir_len) {
		char *p = libdirname+strlen(libdirname);
		*p++ = '\\';
		strncpy(p, p_script_info->zippath, lib_dir_len-1);
		p += lib_dir_len-1;
		*p++ = '\0';
	}
	/* Fully-qualify it */
	GetFullPathName(libdirname, sizeof(libdirname), libdirname, &fname);
}

// Set the Python path before initialization
static int set_path_early()
{
	char *ppath;
	Py_SetPythonHome(libdirname);
	/* Let Python calculate its initial path, according to the
	   builtin rules */
	ppath = Py_GetPath();
//	printf("Initial path: %s\n", ppath);

	/* We know that Py_GetPath points to writeable memory,
	   so we copy our own path into it.
	*/
	if (strlen(ppath) <= strlen(libdirname) + strlen(pZipBaseName) + 1) {
		/* Um. Not enough space. What now? */
		SystemError(0, "Not enough space for new sys.path");
		return -1;
	}

	strcpy(ppath, libdirname);
	strcat(ppath, "\\");
	strcat(ppath, pZipBaseName);
	return 0;
}

// Set the Python path after initialization
static int set_path_late()
{
	int buflen = strlen(libdirname) + strlen(pZipBaseName) + 2;
	char *ppath = (char *)malloc(buflen);
	PyObject *syspath, *newEntry;
	if (!ppath) {
		SystemError(ERROR_NOT_ENOUGH_MEMORY, "no mem for late sys.path");
		return -1;
	}
	strcpy(ppath, libdirname);
	strcat(ppath, "\\");
	strcat(ppath, pZipBaseName);
	syspath = PySys_GetObject("path");
	newEntry = PyString_FromString(ppath);
	if (newEntry) {
		PyList_Append(syspath, newEntry);
		Py_DECREF(newEntry);
	}
	free(ppath);
	return 0;
}


/*
 * returns an error code if initialization fails
 */
int init_with_instance(HMODULE hmod, char *frozen)
{
	int rc;
	if (!_LocateScript(hmod))
		return 255;

	if (!_LoadPythonDLL(hmod))
		return 255;
	if (p_script_info->unbuffered) {
#if defined(MS_WINDOWS) || defined(__CYGWIN__)
		_setmode(fileno(stdin), O_BINARY);
		_setmode(fileno(stdout), O_BINARY);
#endif
#ifdef HAVE_SETVBUF
		setvbuf(stdin,	(char *)NULL, _IONBF, BUFSIZ);
		setvbuf(stdout, (char *)NULL, _IONBF, BUFSIZ);
		setvbuf(stderr, (char *)NULL, _IONBF, BUFSIZ);
#else /* !HAVE_SETVBUF */
		setbuf(stdin,  (char *)NULL);
		setbuf(stdout, (char *)NULL);
		setbuf(stderr, (char *)NULL);
#endif /* !HAVE_SETVBUF */
	}

	if (getenv("PY2EXE_VERBOSE"))
		Py_VerboseFlag = atoi(getenv("PY2EXE_VERBOSE"));
	else
		Py_VerboseFlag = 0;

	Py_IgnoreEnvironmentFlag = 1;
	Py_NoSiteFlag = 1;
	Py_OptimizeFlag = p_script_info->optimize;

	Py_SetProgramName(modulename);

	calc_path();

	if (!Py_IsInitialized()) {
		// First time round and the usual case - set sys.path
		// statically.
		rc = set_path_early();
		if (rc != 0)
			return rc;
	
	//	printf("Path before Py_Initialize(): %s\n", Py_GetPath());
	
		Py_Initialize();
	//	printf("Path after Py_Initialize(): %s\n", PyString_AsString(PyObject_Str(PySys_GetObject("path"))));
		/* Set sys.frozen so apps that care can tell.
		   If the caller did pass NULL, sys.frozen will be set zo True.
		   If a string is passed this is used as the frozen attribute.
		   run.c passes "console_exe", run_w.c passes "windows_exe",
		   run_dll.c passes "dll"
		*/
		if (frozen == NULL)
			PySys_SetObject("frozen", PyBool_FromLong(1));
		else {
			PyObject *o = PyString_FromString(frozen);
			if (o) {
				PySys_SetObject("frozen", o);
				Py_DECREF(o);
			}
		}
	} else {
		// Python already initialized.  This likely means there are
		// 2 py2exe based apps in the same process (eg, 2 COM objects
		// in a single host, 2 ISAPI filters in the same site, ...)
		// Until we get a better answer, add what we need to sys.path
		rc = set_path_late();
		if (rc != 0)
			return rc;
	}

	_TryLoadZlib(hmod);

	return 0;
}

int init(char *frozen)
{
	return init_with_instance(NULL, frozen);
}

void fini(void)
{
	/* The standard Python 2.3 does also allow this: Set PYTHONINSPECT
	   in the script and examine it afterwards
	*/
	if (getenv("PYTHONINSPECT") && Py_FdIsInteractive(stdin, "<stdin>"))
		PyRun_InteractiveLoop(stdin, "<stdin>");
	/* Clean up */
	Py_Finalize();
}

int start (int argc, char **argv)
{
	int rc;
	PyObject *new_path;
	PySys_SetArgv(argc, argv);
	// PySys_SetArgv munged the path - specifically, it added the
	// directory of argv[0] at the start of sys.path.
	// Create a new list object for the path, and rely on our
	// implementation knowledge of set_path above, which writes into
	// the static Py_GetPath() buffer (Note: Py_GetPath() does *not*
	// return the current sys.path value - its just a static buffer
	// holding the initial Python paths)
	new_path = PyList_New(1);
	if (new_path) {
		PyObject *entry = PyString_FromString(Py_GetPath());
		if (entry && (0==PyList_SetItem(new_path, 0, entry)))
			PySys_SetObject("path", new_path);
		Py_DECREF(new_path);
	}
	rc = run_script();
	fini();
	return rc;
}

int run_script(void)
{
	int rc = 0;

	/* load the code objects to execute */
	PyObject *m=NULL, *d=NULL, *seq=NULL;
	/* We execute then in the context of '__main__' */
	m = PyImport_AddModule("__main__");
	if (m) d = PyModule_GetDict(m);
	if (d) seq = PyMarshal_ReadObjectFromString(pScript, numScriptBytes);
	if (seq) {
		Py_ssize_t i, max = PySequence_Length(seq);
		for (i=0;i<max;i++) {
			PyObject *sub = PySequence_GetItem(seq, i);
			if (sub /*&& PyCode_Check(sub) */) {
				PyObject *discard = PyEval_EvalCode((PyCodeObject *)sub,
								    d, d);
				if (!discard) {
					PyErr_Print();
					rc = 255;
				}
				Py_XDECREF(discard);
				/* keep going even if we fail */
			}
			Py_XDECREF(sub);
		}
	}
	return rc;
}

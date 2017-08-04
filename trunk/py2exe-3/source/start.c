/*
 *	   Copyright (c) 2000 - 2013 Thomas Heller
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
#include <shlobj.h>
#include <Python.h>
#include <marshal.h>

#include "MyLoadLibrary.h"
#include "python-dynload.h"

#include <fcntl.h>


struct scriptinfo {
	int tag;
	int optimize;
	int unbuffered;
	int data_bytes;

	char zippath[0];
};

PyMODINIT_FUNC PyInit__memimporter(void);
extern void SystemError(int error, char *msg);

int run_script(void);
void fini(void);
char *pScript;
char *pZipBaseName;
int numScriptBytes;
wchar_t modulename[_MAX_PATH + _MAX_FNAME + _MAX_EXT]; // from GetModuleName()
wchar_t dirname[_MAX_PATH]; // directory part of GetModuleName()
// Hm, do we need this? wchar_t libdirname[_MAX_PATH]; // library directory - probably same as above.
wchar_t libfilename[_MAX_PATH + _MAX_FNAME + _MAX_EXT]; // library filename
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

/*
  Calculate the directory name where of the executable
 */
BOOL calc_dirname(HMODULE hmod)
{
	int is_special;
	wchar_t *modulename_start;
	wchar_t *cp;

	// get module filename
	if (!GetModuleFileNameW(hmod, modulename, sizeof(modulename))) {
		SystemError(GetLastError(), "Retrieving module name");
		return FALSE;
	}
	// get directory of modulename.  Note that in some cases
	// (eg, ISAPI), GetModuleFileName may return a leading "\\?\"
	// (which is a special format you can pass to the Unicode API
	// to avoid MAX_PATH limitations).  Python currently can't understand
	// such names, and as it uses the ANSI API, neither does Windows!
	// So fix that up here.
	is_special = wcslen(modulename) > 4 &&
		wcsncmp(modulename, L"\\\\?\\", 4)==0;
	modulename_start = is_special ? modulename + 4 : modulename;
	wcscpy(dirname, modulename_start);
	cp = wcsrchr(dirname, L'\\');
	*cp = L'\0';
	return TRUE;
}

/*
  The executable contains a scriptinfo structure as a resource.
  
  This structure contains some flags for the Python interpreter, the pathname
  of the library relative to the executable (if the pathname is empty the
  executable is the library itself), and marshalled byte string which is a
  Python list of code objects that we have to execute.

  The first code objects contain some bootstrap code for py2exe, the last
  one contains the main script that should be run.
  
  This function loads the structure from the resource, sets the pScript
  pointer to the start of the marshalled byte string, and fills in the global
  variable 'libfilename' with the absolute pathname of the library file.
 */
BOOL locate_script(HMODULE hmod)
{
	HRSRC hrsrc = FindResourceA(hmod, MAKEINTRESOURCEA(1), "PYTHONSCRIPT");
	HGLOBAL hgbl;

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
	pScript = p_script_info->zippath + strlen(p_script_info->zippath) + 1;

	// get full pathname of the 'library.zip' file
	if (p_script_info->zippath[0]) {
		_snwprintf(libfilename, sizeof(libfilename),
			   L"%s\\%S", dirname, p_script_info->zippath);
	} else {
		GetModuleFileNameW(hmod, libfilename, sizeof(libfilename));
	}
	// if needed, libdirname should be initialized here.
	return TRUE; // success
}

/*
  Examine the PYTHONINSPECT environment variable (which may have been set by
  the python script itself), run an interactive Python interpreter if it is
  set, and finally call Py_Finalize().
 */
void fini(void)
{
	/* The standard Python does also allow this: Set PYTHONINSPECT
	   in the script and examine it afterwards
	*/
	if (getenv("PYTHONINSPECT") && Py_FdIsInteractive(stdin, "<stdin>"))
		PyRun_InteractiveLoop(stdin, "<stdin>");
	/* Clean up */
	Py_Finalize();
}

/*
  This function creates the __main__ module and runs the bootstrap code and
  the main Python script.
 */
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
		for (i=0; i<max; i++) {
			PyObject *sub = PySequence_GetItem(seq, i);
			if (sub /*&& PyCode_Check(sub) */) {
				PyObject *discard = PyEval_EvalCode(sub, d, d);
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


/* XXX XXX XXX flags should be set elsewhere */
/*
  c:\Python34\include\Python.h

PyAPI_DATA(int) Py_DebugFlag;
PyAPI_DATA(int) Py_VerboseFlag;
PyAPI_DATA(int) Py_QuietFlag;
PyAPI_DATA(int) Py_InteractiveFlag;
PyAPI_DATA(int) Py_InspectFlag;
PyAPI_DATA(int) Py_OptimizeFlag;
PyAPI_DATA(int) Py_NoSiteFlag;
PyAPI_DATA(int) Py_BytesWarningFlag;
PyAPI_DATA(int) Py_UseClassExceptionsFlag;
PyAPI_DATA(int) Py_FrozenFlag;
PyAPI_DATA(int) Py_IgnoreEnvironmentFlag;
PyAPI_DATA(int) Py_DontWriteBytecodeFlag;
PyAPI_DATA(int) Py_NoUserSiteDirectory;
PyAPI_DATA(int) Py_UnbufferedStdioFlag;
PyAPI_DATA(int) Py_HashRandomizationFlag;
PyAPI_DATA(int) Py_IsolatedFlag;

 */
void set_vars(HMODULE hmod_pydll)
{
	int *pflag;

/* I'm not sure if the unbuffered code really works... */
	if (p_script_info->unbuffered) {
		_setmode(_fileno(stdin), O_BINARY);
		_setmode(_fileno(stdout), O_BINARY);
		setvbuf(stdin,	(char *)NULL, _IONBF, 0);
		setvbuf(stdout, (char *)NULL, _IONBF, 0);
		setvbuf(stderr, (char *)NULL, _IONBF, 0);

		pflag = (int *)MyGetProcAddress(hmod_pydll, "Py_UnbufferedStdioFlag");
		if (pflag) *pflag = 1;
	}

	pflag = (int *)MyGetProcAddress(hmod_pydll, "Py_IsolatedFlag");
	if (pflag) *pflag = 1;

	pflag = (int *)MyGetProcAddress(hmod_pydll, "Py_NoSiteFlag");
	if (pflag) *pflag = 1;

	pflag = (int *)MyGetProcAddress(hmod_pydll, "Py_IgnoreEnvironmentFlag");
	if (pflag) *pflag = 1;

	pflag = (int *)MyGetProcAddress(hmod_pydll, "Py_NoUserSiteDirectory");
	if (pflag) *pflag = 1;

	pflag = (int *)MyGetProcAddress(hmod_pydll, "Py_OptimizeFlag");
	if (pflag) *pflag = p_script_info->optimize;

	pflag = (int *)MyGetProcAddress(hmod_pydll, "Py_VerboseFlag");
	if (pflag) {
		if (getenv("PY2EXE_VERBOSE"))
			*pflag = atoi(getenv("PY2EXE_VERBOSE"));
		else
			*pflag = 0;
	}
}

/*
  Load the Python DLL, either from the resource in the library file (if found),
  or from the file system.
  
  This function should also be used to get all the function pointers that
  python3.c needs at once.
 */
HMODULE load_pythondll(void)
{
	HMODULE hmod_pydll;
	HANDLE hrsrc;
	HMODULE hmod = LoadLibraryExW(libfilename, NULL, LOAD_LIBRARY_AS_DATAFILE);

	// Try to locate pythonxy.dll as resource in the exe
	hrsrc = FindResourceA(hmod, MAKEINTRESOURCEA(1), PYTHONDLL);
	if (hrsrc) {
		HGLOBAL hgbl;
		DWORD size;
		char *ptr;
		hgbl = LoadResource(hmod, hrsrc);
		size = SizeofResource(hmod, hrsrc);
		ptr = LockResource(hgbl);
		hmod_pydll = MyLoadLibrary(PYTHONDLL, ptr, NULL);
	} else
		/*
		  XXX We should probably call LoadLibraryEx with
		  LOAD_WITH_ALTERED_SEARCH_PATH so that really our own one is
		  used.
		 */
		hmod_pydll = LoadLibraryA(PYTHONDLL);
	FreeLibrary(hmod);
	return hmod_pydll;
}

int init_with_instance(HMODULE hmod_exe, char *frozen)
{

	int rc = 0;
	HMODULE hmod_pydll;

/*	Py_NoSiteFlag = 1; /* Suppress 'import site' */
/*	Py_InspectFlag = 1; /* Needed to determine whether to exit at SystemExit */

	calc_dirname(hmod_exe);
//	wprintf(L"modulename %s\n", modulename);
//	wprintf(L"dirname %s\n", dirname);

	if (!locate_script(hmod_exe)) {
		SystemError(-1, "FATAL ERROR: Could not locate script");
//		printf("FATAL ERROR locating script\n");
		return -1;
	}

	hmod_pydll = load_pythondll();
	if (hmod_pydll == NULL) {
		SystemError(-1, "FATAL ERROR: Could not load python library");
//		printf("FATAL Error: could not load python library\n");
		return -1;
	}
	if (PythonLoaded(hmod_pydll) < 0) {
		SystemError(-1, "FATAL ERROR: Failed to load some Python symbols");
//		printf("FATAL Error: failed to load some Python symbols\n");
		return -1;
	}

	set_vars(hmod_pydll);

	/*
	  _memimporter contains the magic which allows to load
	  dlls from memory, without unpacking them to the file-system.

	  It is compiled into all the exe-stubs.
	*/
	PyImport_AppendInittab("_memimporter", PyInit__memimporter);

	/*
	  Start the ball rolling.
	*/
	Py_SetProgramName(modulename);
	Py_SetPath(libfilename);
	Py_Initialize();


	/* Set sys.frozen so apps that care can tell.  If the caller did pass
	   NULL, sys.frozen will be set to 'True'.  If a string is passed this
	   is used as the frozen attribute.  run.c passes "console_exe",
	   run_w.c passes "windows_exe", run_dll.c passes "dll" This falls
	   apart when you consider that in some cases, a single process may
	   end up with two py2exe generated apps - but still, we reset frozen
	   to the correct 'current' value for the newly initializing app.
	*/
	if (frozen == NULL)
		PySys_SetObject("frozen", PyBool_FromLong(1));
	else {
		PyObject *o = PyUnicode_FromString(frozen);
		if (o) {
			PySys_SetObject("frozen", o);
			Py_DECREF(o);
		}
	}
	return rc;
}

int init(char *frozen)
{
	return init_with_instance(NULL, frozen);
}

static PyObject *Py_MessageBox(PyObject *self, PyObject *args)
{
	HWND hwnd;
	char *message;
	char *title = NULL;
	int flags = MB_OK;

	if (!PyArg_ParseTuple(args, "is|zi", &hwnd, &message, &title, &flags))
		return NULL;
	return PyLong_FromLong(MessageBoxA(hwnd, message, title, flags));
}

static PyObject *Py_SHGetSpecialFolderPath(PyObject *self, PyObject *args)
{
	wchar_t path[MAX_PATH];
	int nFolder;
	if (!PyArg_ParseTuple(args, "i", &nFolder))
		return NULL;
	SHGetSpecialFolderPathW(NULL, path, nFolder, TRUE);
	return PyUnicode_FromWideChar(path, -1);
}

PyMethodDef method[] = {
	{ "_MessageBox", Py_MessageBox, METH_VARARGS },
	{ "_SHGetSpecialFolderPath", Py_SHGetSpecialFolderPath, METH_VARARGS },
};


int start(int argc, wchar_t **argv)
{
	int rc;
	PyObject *mod;
	PySys_SetArgvEx(argc, argv, 0);

	mod = PyImport_ImportModule("sys");
	if (mod) {
		PyObject_SetAttrString(mod,
				       method[0].ml_name,
				       PyCFunction_New(&method[0], NULL));
		PyObject_SetAttrString(mod,
				       method[1].ml_name,
				       PyCFunction_New(&method[1], NULL));
	}

	rc = run_script();
	fini();
	return rc;
}

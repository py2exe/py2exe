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

static BOOL _LocateScript(HMODULE hmod)
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

static BOOL _LoadPythonDLL(HMODULE hmod)
{
	HRSRC hrsrc;
	char buffer[32];
	FILE *fp;

	// Try to locate pythonxy.dll as resource in the exe
	hrsrc = FindResource(hmod, MAKEINTRESOURCE(1), PYTHONDLL);
	if (hrsrc) {
		HGLOBAL hgbl = LoadResource(hmod, hrsrc);
		if (!_load_python(PYTHONDLL, LockResource(hgbl))) {
			SystemError(GetLastError(), "Could not load python dll");
			return FALSE;
		}
		return TRUE;
	}

	// Try to load pythonxy.dll from the start of the library.zip file
	fp = fopen(libfilename, "rb");
	if (fp == NULL) {
		SystemError(0, "Could not open zipfile for reading");
		return FALSE;
	}
	memset(buffer, 0, sizeof(buffer));
	if (11 != fread(buffer, 1, 11, fp)) {
		SystemError(0, "Could not read data from zipfile");
		return FALSE;
	}
	if (0 == strcmp(buffer, "<pythondll>")) {
		int nBytes, res;
		char *p;

		fread(&nBytes, 1, sizeof(int), fp);
		p = malloc(nBytes);
		if (p == NULL) {
			SystemError(0, "Could not allocate memory for pythondll");
			return FALSE;
		}
		fread(p, 1, nBytes, fp);
		fclose(fp);
		res = _load_python(PYTHONDLL, p);
		free(p);
		if (!res) {
			SystemError(GetLastError(), "Could not load python dll");
			return FALSE;
		}
		return TRUE;
	}
	// try to load pythonxy.dll from the file system
	{
		char buffer[_MAX_PATH + _MAX_FNAME + _MAX_EXT];
		snprintf(buffer, sizeof(buffer), "%s\\%s", dirname, PYTHONDLL);
		printf("*** LoadLibrary %s\n", buffer);
		if (!_load_python(buffer, NULL)) {
			SystemError(GetLastError(), "LoadLibrary(pythondll) failed");
			return FALSE;
		}
	}
	return TRUE;
}

/*
 * returns an error code if initialization fails
 */
int init_with_instance(HMODULE hmod, char *frozen)
{
	if (!_LocateScript(hmod))
		return 255;

	if (!_LoadPythonDLL(hmod))
		return 255;

	printf("dirname '%s', zippath '%s'\n", dirname, p_script_info->zippath);
	printf("SUCCESS _load_python(" PYTHONDLL ")\n");
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
	/* From Barry Scott */
	/* Must not set the PYTHONHOME env var as this prevents
	   python being used in os.system or os.popen */
	Py_SetPythonHome(libdirname);

/*
 * PYTHONPATH entries will be inserted in front of the
 * standard python path.
 */
/*
 * We need the module's directory, because zipimport needs zlib.pyd.
 * And, of course, the zipfile itself.
 */
	{
		char buffer[_MAX_PATH * 3 + 256];
		sprintf(buffer, "PYTHONPATH=%s;%s\\%s",
			libdirname, libdirname, pZipBaseName);
		_putenv (buffer);
	}
	_putenv ("PYTHONSTARTUP=");
	_putenv ("PYTHONOPTIMIZE=");
	_putenv ("PYTHONDEBUG=");
	_putenv("PYTHONINSPECT=");

	if (getenv("PY2EXEVERBOSE")) 
		_putenv ("PYTHONVERBOSE=1");
	else
		_putenv ("PYTHONVERBOSE=");

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
 

	Py_NoSiteFlag = 1;
	Py_OptimizeFlag = p_script_info->optimize;

	/* XXX Is this correct? For the dll server code? */
	/* And we should probably change all the above code if Python is already
	 * initialized */
	Py_SetProgramName(modulename);

	Py_Initialize();

	/* From Barry Scott */
	/* cause python to calculate the path */
	Py_GetPath();
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
	/* clean up the environment so that os.system
	   and os.popen processes can run python the normal way */
	/* Hm, actually it would be better to set them to values saved before
	   changing them ;-) */
	_putenv("PYTHONPATH=");
	_putenv("PYTHONVERBOSE=");
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
	PySys_SetArgv(argc, argv);
	rc = run_script();
	fini();
	return rc;
}

int run_script(void)
{
	int rc;
	char buffer[_MAX_PATH * 3];
	snprintf(buffer, sizeof(buffer),
		 "import sys; sys.path=[r\"\"\"%s\\%s\"\"\"]; del sys",
		 libdirname, pZipBaseName);
	rc = PyRun_SimpleString(buffer);
	if (rc == 0) {
		/* load the code objects to execute */
		PyObject *m=NULL, *d=NULL, *seq=NULL;
		/* We execute then in the context of '__main__' */
		m = PyImport_AddModule("__main__");
		if (m) d = PyModule_GetDict(m);
		if (d) seq = PyMarshal_ReadObjectFromString(pScript, numScriptBytes);
		if (seq) {
			int i, max = PySequence_Length(seq);
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
	}
	return rc;
}

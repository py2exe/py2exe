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
#include <Python.h>
#include <marshal.h>
#include <compile.h>
#include <eval.h>
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
char dirname[_MAX_PATH]; // my directory
char libdirname[_MAX_PATH]; // library directory - probably same as above.
char modulename[_MAX_PATH];
struct scriptinfo *p_script_info;

/*
 * returns an error code if initialization fails
 */
int init_with_instance(HMODULE hmod, char *frozen)
{
	/* Open the executable file and map it to memory */
	if(!GetModuleFileName(hmod, modulename, sizeof(modulename))) {
		SystemError(GetLastError(), "Retrieving module name");
		return 255;
	}
	{
		char *cp;
		strcpy(dirname, modulename);
		cp = strrchr(dirname, '\\');
		*cp = '\0';
	}

	{
		HRSRC hrsrc = FindResource(hmod, MAKEINTRESOURCE(1), "PYTHONSCRIPT");
		HGLOBAL hgbl;

		if (!hrsrc) {
			SystemError (GetLastError(), "Could not locate script resource:");
			return 255;
		}
		hgbl = LoadResource(hmod, hrsrc);
		if (!hgbl) {
			SystemError (GetLastError(), "Could not load script resource:");
			return 255;
		}
		p_script_info = (struct scriptinfo *)pScript = LockResource(hgbl);
		if (!pScript)  {
			SystemError (GetLastError(), "Could not lock script resource:");
			return 255;
		}
	}
	numScriptBytes = p_script_info->data_bytes;
	pScript += sizeof(struct scriptinfo);
	if (p_script_info->tag != 0x78563412) {
		SystemError (0, "Bug: Invalid script resource");
		return 255;
	}
	pScript += strlen(p_script_info->zippath) + 1;
	{
		/* If the zip path has any path component, then build our Python
		   home directory from that.
		*/
		char buffer[_MAX_PATH * 3 + _MAX_FNAME + _MAX_EXT];
		char *fname;
		int lib_dir_len;
		pZipBaseName = pScript - 1;
		while (pZipBaseName > p_script_info->zippath && \
		       *(pZipBaseName-1) != '\\')
			pZipBaseName--;
		strcpy(libdirname, dirname);
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
		sprintf(buffer, "PYTHONPATH=%s;%s\\%s",
			libdirname, libdirname, pZipBaseName);
		_putenv (buffer);
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
		PySys_SetObject("frozen", Py_True);
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
				if (sub && PyCode_Check(sub)) {
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

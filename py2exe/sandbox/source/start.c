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
#include <windows.h>

extern void SystemError(int error, char *msg);
run_script(void);
void fini(void);
char *pScript;

/*
 * returns an error code if initialization fails
 */
int init_with_instance(HMODULE hmod)
{
    int result = 255;
    char modulename[_MAX_PATH];
    char dirname[_MAX_PATH];
    
    /* Open the executable file and map it to memory */
    if(!GetModuleFileName(hmod, modulename, sizeof(modulename))) {
	SystemError(GetLastError(), "Retrieving module name");
	return result;
    }
    {
	char *cp;
	strcpy(dirname, modulename);
	cp = strrchr(dirname, '\\');
	*cp = '\0';
    }
    
    {
	HRSRC hrsrc = FindResource(NULL, MAKEINTRESOURCE(1), "PYTHONSCRIPT");
	HGLOBAL hgbl;

	if (!hrsrc) {
	    SystemError (GetLastError(), "Could not locate script resource:");
	    return 1;
	}
	hgbl = LoadResource(NULL, hrsrc);
	if (!hgbl) {
	    SystemError (GetLastError(), "Could not load script resource:");
	    return 1;
	}
	pScript = LockResource(hgbl);
	if (!pScript)  {
	    SystemError (GetLastError(), "Could not lock script resource:");
	    return 1;
	}
    }
    {
	char buffer[_MAX_PATH + 32];
	/* From Barry Scott */
	/* Must not set the PYTHONHOME env var as this prevents
	   python being used in os.system or os.popen */
	Py_SetPythonHome( dirname );

/*
 * PYTHONPATH entries will be inserted in front of the
 * standard python path.
 */
    /* Todo: Read the zipfile name from the structure at the beginning
       of the script resource or in a separate resource
    */
	sprintf(buffer, "PYTHONPATH=%s\\library.zip", dirname);
	_putenv (buffer);
//	fprintf(stderr, "SETENV %s\n", buffer);
	_putenv ("PYTHONSTARTUP=");
	_putenv ("PYTHONOPTIMIZE=");
	_putenv ("PYTHONVERBOSE=");
	_putenv ("PYTHONUNBUFFERED=");
	_putenv ("PYTHONINSPECT=");
	_putenv ("PYTHONDEBUG=");
    }

    Py_NoSiteFlag = 1;
    /* Todo: Read useful flags from a structure which either is at the beginning
       of the script resource or in a separate resource
    */
//    Py_VerboseFlag = p_script_info->verbose;
//    Py_OptimizeFlag = p_script_info->optimize;
/*
potentially useful:
(int) Py_VerboseFlag;
(int) Py_InteractiveFlag;
(int) Py_OptimizeFlag;
(int) Py_NoSiteFlag;
(int) Py_DivisionWarningFlag;
(int) Py_IgnoreEnvironmentFlag;
not useful imo:
(int) Py_TabcheckFlag;
(int) Py_DebugFlag;
(int) Py_UseClassExceptionsFlag;
dont know what these do:
(int) Py_UnicodeFlag;
(int) Py_FrozenFlag;
*/
    Py_SetProgramName(modulename);

    Py_Initialize();

    /* From Barry Scott */
    /* cause python to calculate the path */
    Py_GetPath();
    /* clean up the environment so that os.system
       and os.popen processes can run python */
    _putenv( "PYTHONPATH=" );	

    return 0;
}

int init(void)
{
    return init_with_instance(NULL);
}

void fini(void)
{
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
    PyRun_SimpleString("import sys; sys.path=sys.path[:2]");
//    fprintf(stderr, "\nPath is now %s\n\n", PySys_GetPath());
    PyRun_SimpleString(pScript);
    return 0;
}

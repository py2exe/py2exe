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

struct scriptinfo {
    int tag;
    int optimize;
    int unbuffered;

    char zippath[0];
};

extern void SystemError(int error, char *msg);
run_script(void);
void fini(void);
char *pScript;
char dirname[_MAX_PATH];
char modulename[_MAX_PATH];
struct scriptinfo *p_script_info;

/*
 * returns an error code if initialization fails
 */
int init_with_instance(HMODULE hmod)
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

    pScript += sizeof(struct scriptinfo);
    if (p_script_info->tag != 0x78563412) {
	    SystemError (0, "Bug: Invalid script resource");
	    return 255;
    }
    pScript += strlen(p_script_info->zippath) + 1;

    {
	char buffer[_MAX_PATH + 32];
	/* From Barry Scott */
	/* Must not set the PYTHONHOME env var as this prevents
	   python being used in os.system or os.popen */
	Py_SetPythonHome(dirname);

/*
 * PYTHONPATH entries will be inserted in front of the
 * standard python path.
 */
/*
 * We need the module's directory, because zipimport needs zlib.pyd.
 * And, of course, the zipfile itself.
 */
	sprintf(buffer, "PYTHONPATH=%s;%s\\%s", dirname, dirname, p_script_info->zippath);
	_putenv (buffer);
	_putenv ("PYTHONSTARTUP=");
	_putenv ("PYTHONOPTIMIZE=");

	if (getenv("PY2EXEVERBOSE"))
	    _putenv ("PYTHONVERBOSE=1");
	else
	    _putenv ("PYTHONVERBOSE");

	if (p_script_info->unbuffered)
	    _putenv ("PYTHONUNBUFFERED=1");
	else
	    _putenv ("PYTHONUNBUFFERED=");

	_putenv ("PYTHONDEBUG=");
    }

    Py_NoSiteFlag = 1;
    Py_OptimizeFlag = p_script_info->optimize;
    
//    Py_VerboseFlag = p_script_info->verbose;

    /* XXX Is this correct? For the dll server code? */
    /* And we should probably change all the above code if Python is already
     * initialized */
    Py_SetProgramName(modulename);

    Py_Initialize();

    /* From Barry Scott */
    /* cause python to calculate the path */
    Py_GetPath();
    /* clean up the environment so that os.system
       and os.popen processes can run python the normal way */
    _putenv( "PYTHONPATH=" );	
    _putenv ("PYTHONUNBUFFERED=");

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
    int rc;
    /* It would be nice to run only with the single zipfile entry on sys.path,
       but it seems for inproc com servers the module's directory is needed as well.
    */
    char buffer[_MAX_PATH * 3];
    snprintf(buffer, sizeof(buffer),
	     "import sys; sys.path=[r'%s', r'%s\\%s']",
	     dirname,
	     dirname, p_script_info->zippath);
    rc = PyRun_SimpleString(buffer);
    if (rc != 0)
	return rc;
    return PyRun_SimpleString(pScript);
}

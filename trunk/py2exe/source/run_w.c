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

#include <windows.h>
#include <stdio.h>
#include "Python-dynload.h"

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

extern int init(char *);
extern int start(int argc, char **argv);
extern void init_memimporter(void);

static PyObject *Py_MessageBox(PyObject *self, PyObject *args)
{
	HWND hwnd;
	char *message;
	char *title = NULL;
	int flags = MB_OK;

	if (!PyArg_ParseTuple(args, "is|zi", &hwnd, &message, &title, &flags))
		return NULL;
	return PyInt_FromLong(MessageBox(hwnd, message, title, flags));
}

PyMethodDef method[] = {
	{ "_MessageBox", Py_MessageBox, METH_VARARGS }
};

int WINAPI
WinMain(HINSTANCE hInst, HINSTANCE hPrevInst,
	LPSTR lpCmdLine, int nCmdShow)
{
	int result;
	PyObject *mod;

	result = init("windows_exe");
	if (result)
		return result;

	init_memimporter();
	mod = PyImport_ImportModule("sys");
	if (mod)
		PyObject_SetAttrString(mod,
				       "_MessageBox",
				       PyCFunction_New(&method[0], NULL));
	return start(__argc, __argv);
}

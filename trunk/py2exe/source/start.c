/*
 * $Id$
 *
 */
#include <Python.h>
#include <windows.h>
#include "archive.h"
#include "zlib.h"

#define SCRIPT_INFO_TAG 0x0bad3bad

struct script_info {
    int module_mapping_length;
    int optimize;
    int verbose;
    int tag;
};

char *arc_data;	/* memory mapped archive */
DWORD arc_size;	/* number of bytes in archive */
PyObject *toc;	/* Dictionary mapping filenames to file offsets */

struct script_info *p_script_info;

extern void SystemError(int error, char *msg);

static char *MapExistingFile(char *pathname, DWORD *psize)
{
    HANDLE hFile, hFileMapping;
    DWORD nSizeLow, nSizeHigh;
    char *data;
    
    hFile = CreateFile(pathname,
		       GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING,
		       FILE_ATTRIBUTE_NORMAL, NULL);
    if(hFile == INVALID_HANDLE_VALUE)
	return NULL;
    nSizeLow = GetFileSize(hFile, &nSizeHigh);
    hFileMapping = CreateFileMapping(hFile,
				     NULL, PAGE_READONLY, 0, 0, NULL);
    CloseHandle(hFile);
    
    if(hFileMapping == INVALID_HANDLE_VALUE)
	return NULL;
    
    data = MapViewOfFile(hFileMapping,
			 FILE_MAP_READ, 0, 0, 0);
    
    CloseHandle(hFileMapping);
    *psize = nSizeLow;
    return data;
}

char *
extract_data (char *src, int method, int comp_size,
	      int uncomp_size)
{
    z_stream zstream;
    char *dst;

    dst = malloc(uncomp_size + 1);
    if (!dst)
	return NULL;

    if (method == Z_DEFLATED) {
	int x;
        memset (&zstream, 0, sizeof (zstream));
        zstream.next_in = src;
        zstream.avail_in = comp_size+1;
	zstream.next_out = dst;
        zstream.avail_out = uncomp_size;

/* Apparently an undocumented feature of zlib: Set windowsize
 to negative values to supress the gzip header and be compatible with
 zip! */
        if (Z_OK != (x = inflateInit2(&zstream, -15)))
	    goto cleanup;
	if (Z_STREAM_END != (x = inflate(&zstream, Z_FINISH)))
	    goto cleanup;
	if (Z_OK != (x = inflateEnd(&zstream)))
	    goto cleanup;
    } else if (method == 0) {
	memcpy(dst, src, uncomp_size);
    }
    return dst;
  cleanup:
    free(dst);
    return NULL;
}

char *
GetContentsFromOffset(long pos, char *data, int size, int *psize)
{
    char *pcomp;

    /* read the end of central directory record */
    struct eof_cdir *pe = (struct eof_cdir *)&data[size - sizeof
						  (struct eof_cdir)];
    int arc_start = size - sizeof (struct eof_cdir) - pe->nBytesCDir -
	pe->ofsCDir;
    struct cdir *pcdir = (struct cdir *)&data[pos];
    struct fhdr *pfhdr = (struct fhdr *)&data[pcdir->ofs_local_header +
					     arc_start];
    
    if (pcdir->tag != 0x02014b50)
	return NULL;
    if (pfhdr->tag != 0x04034b50)
	return NULL;
    pos += sizeof(struct cdir) + pcdir->fname_length + pcdir->extra_length +
	pcdir->comment_length;
    
    pcomp = &data[pcdir->ofs_local_header
		 + sizeof (struct fhdr)
		 + arc_start
		 + pfhdr->fname_length
		 + pfhdr->extra_length];
    
    *psize = pcdir->uncomp_size;
    return extract_data(pcomp, pfhdr->method,
			pcdir->comp_size, pcdir->uncomp_size);
}

char *GetContents(char *name, char *data, int size, int *psize)
{
    PyObject *pos = PyDict_GetItemString(toc, name);
    if (!pos) {
	PyErr_SetString(PyExc_KeyError, name);
	return NULL;
    }
    return GetContentsFromOffset(PyInt_AsLong(pos), data, size, psize);
}

void fix_path(char *src)
{
    while (*src) {
	if (*src == '/')
	    *src = '\\';
	++src;
    }
}

BOOL
GetScriptInfo(char *data, int size)
{
    /* read the end of central directory record */
    struct eof_cdir *pe = (struct eof_cdir *)&data[size - sizeof
						  (struct eof_cdir)];

    int arc_start = size - sizeof (struct eof_cdir) - pe->nBytesCDir -
	pe->ofsCDir;

    int ofs = arc_start - sizeof (struct script_info);

    /* read meta_data info */
    p_script_info =  (struct script_info *)&data[ofs];

    if (p_script_info->tag != SCRIPT_INFO_TAG || ofs < 0)
	return FALSE;

    return TRUE;
}

PyObject *
BuildToc(char *data, int size)
{
    int n;
    PyObject *dict = PyDict_New();

    /* read the end of central directory record */
    struct eof_cdir *pe = (struct eof_cdir *)&data[size - sizeof
						  (struct eof_cdir)];

    int arc_start = size - sizeof (struct eof_cdir) - pe->nBytesCDir -
	pe->ofsCDir;

    /* set position to start of central directory */
    int pos = arc_start + pe->ofsCDir;

    int ofs = arc_start - sizeof (struct script_info);
    
    /* make sure this is a zip file */
    if (pe->tag != 0x06054b50)
	return NULL;
    
    /* Loop through the central directory, reading all entries */
    for (n = 0; n < pe->nTotalCDir; ++n) {
	char *fname;
	char *pcomp;
	int nextpos;
	struct cdir *pcdir = (struct cdir *)&data[pos];
	struct fhdr *pfhdr = (struct fhdr *)&data[pcdir->ofs_local_header +
						 arc_start];

        if (pcdir->tag != 0x02014b50)
	    return NULL;
	if (pfhdr->tag != 0x04034b50)
	    return NULL;
	nextpos = pos + sizeof (struct cdir);
	fname = (char *)&data[nextpos]; /* This is not null terminated! */
	nextpos += pcdir->fname_length + pcdir->extra_length +
	    pcdir->comment_length;

	pcomp = &data[pcdir->ofs_local_header
		     + sizeof (struct fhdr)
		     + arc_start
		     + pfhdr->fname_length
		     + pfhdr->extra_length];

	/* XXX Problem:
	 * info-zip's zip program uses '/' as separator,
	 * zipfile.py uses '\' (or does it use os.sep?
	 */
#if 1
	{
	    char name[_MAX_PATH];
	    strncpy (name, fname, pcdir->fname_length);
	    name[pcdir->fname_length] = '\0';
	    fix_path(name);
	    PyDict_SetItem(dict,
			   PyString_FromString(name),
			   PyInt_FromLong(pos));
	}
#else
	PyDict_SetItem(dict,
		       PyString_FromStringAndSize(fname, pcdir->fname_length),
		       PyInt_FromLong(pos));
#endif
	pos = nextpos;
    }
    return dict;
}

BOOL Load_Module(char *name)
{
    char *data;
    char buffer[_MAX_PATH];
    int size;

    if (p_script_info->optimize)
	sprintf (buffer, "%s.pyo", name);
    else
	sprintf (buffer, "%s.pyc", name);
    data = GetContents(buffer, arc_data, arc_size, &size);
    if (data) {
	PyObject *marshaldict;
	PyObject *module;
	PyObject *marshal = PyImport_Import("marshal");
	PyObject *loadsfunc;
	PyObject *pdata = PyString_FromStringAndSize(data+8, size-8);

	free(data);
	marshaldict = PyModule_GetDict(marshal); /* Borrowed Ref! */
	loadsfunc = PyDict_GetItemString(marshaldict, "loads"); /* Borrowed Ref! */
	module = PyObject_CallFunction(loadsfunc, "O", pdata);

	PyImport_ExecCodeModule(name, module);

	Py_DECREF(module);
	Py_DECREF(pdata);
	return TRUE;
    } else
	return FALSE;
}

static PyObject *get_code(PyObject *self, PyObject *args)
{
    char *fname;
    int size;
    char *data;
    PyObject *result;

    if (!PyArg_ParseTuple(args, "s", &fname))
	return NULL;
    data = GetContents(fname, arc_data, arc_size, &size);
    if (!data) {
	return NULL;
    }
    result = PyString_FromStringAndSize(data, size);
    free(data);
    return result;
}


static PyMethodDef methods[] =
{
    {"get_code", get_code, 
     METH_VARARGS},
    {NULL, NULL}
};

void fix_string(char *src)
{
    char *dst = src;
    while (*src) {
	if (*src == '\r')
	    ++src;
	*dst++ = *src++;
    }
    *dst = '\0';
}

int start(int argc, char **argv)
{
    int result = 255;
    char modulename[_MAX_PATH];
    char dirname[_MAX_PATH];
    
    /* Open the executable file and map it to memory */
    if(!GetModuleFileName(NULL, modulename, sizeof(modulename))) {
	SystemError(GetLastError(), "Retrieving module name");
	return result;
    }
    {
	char *cp;
	strcpy(dirname, modulename);
	cp = strrchr(dirname, '\\');
	*cp = '\0';
    }
    
    arc_data = MapExistingFile(modulename, &arc_size);
    if(!arc_data) {
	SystemError(GetLastError(), "Opening archive");
	return result;
    }

    if (!GetScriptInfo(arc_data, arc_size)) {
	/* XXX Raise Error */
	SystemError (0, "Could not get Script info\n");
	goto finish;
    }

    {
	char buffer[_MAX_PATH + 32];
/* By settings PYTHONHOME we can convince Python 2.0 NOT
 * to pick up entries from the registry into sys.path.
 * There seems to be no way to avoid this on Python 1.5.
 */
	sprintf(buffer, "PYTHONHOME=%s", dirname);
	_putenv (buffer);
/*
 * PYTHONPATH entries will be inserted in front of the
 * standard python path.
 */
	sprintf(buffer, "PYTHONPATH=%s", dirname);
	_putenv (buffer);

	_putenv ("PYTHONSTARTUP=");
	_putenv ("PYTHONOPTIMIZE=");
	_putenv ("PYTHONVERBOSE=");
	_putenv ("PYTHONUNBUFFERED=");
	_putenv ("PYTHONINSPECT=");
	_putenv ("PYTHONDEBUG=");
    }

    /* Other useful flags? UNBUFFERED? */
    Py_NoSiteFlag = 1;
    Py_VerboseFlag = p_script_info->verbose;
    Py_OptimizeFlag = p_script_info->optimize;
    Py_SetProgramName(modulename);
/* Py_Initialize() will construct the path, and try
 * to import exceptions from this.
 * In Python 2.0, this is a builtin module.
 * In Python 1.5, this is a python module, which must
 * be imported from the file system.
 */
    Py_Initialize();

    PySys_SetArgv(argc, argv);

    toc = BuildToc(arc_data, arc_size);

    {
	char buffer[_MAX_PATH + 32];
	sprintf (buffer, "import sys; sys.path=[r'%s']", dirname);
	PyRun_SimpleString(buffer);
    }
    Load_Module("imputil");
    PyRun_SimpleString("import imputil");

    Py_InitModule("__main__", methods);

    /* Extract support script as string and run it */
    {
	int size;
	char *data = GetContents("Scripts\\support.py",
				 arc_data, arc_size, &size);
	if (data) {
	    char *script = realloc(data, size+2);
	    if (script) {
		data = script;
		script[size] = '\n';
		script[size+1] = '\0';
		fix_string(script);
		PyRun_SimpleString(script);
	    } else {
		SystemError(0, "Not enough memory");
	    }
	    free(data);
	} else {
	    PyErr_Print();
	    goto done;
	}
    }

    /* Extract the script as string and run it */
    {
	int size;
	char *data = GetContents("Scripts\\__main__.py", arc_data, arc_size, &size);
	if (data) {
	    char *script = realloc(data, size+2);
	    if (script) {
		data = script;
		script[size] = '\n';
		script[size+1] = '\0';
		fix_string(script);
		PyRun_SimpleString(script);
	    } else {
		SystemError(0, "Not enough memory");
	    }
	    free(data);
	} else {
	    PyErr_Print();
	    goto done;
	}
    }
  done:
    Py_Finalize();
  finish:
    /* Clean up */
    UnmapViewOfFile (arc_data);
    
    return result;
}

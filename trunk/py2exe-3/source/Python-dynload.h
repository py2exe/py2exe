#define Py_OptimizeFlag *(_Py_OptimizeFlag_PTR())
#define Py_NoSiteFlag *(_Py_NoSiteFlag_PTR())
#define Py_VerboseFlag *(_Py_VerboseFlag_PTR())

extern int *_Py_OptimizeFlag_PTR();
extern int *_Py_NoSiteFlag_PTR();
extern int *_Py_VerboseFlag_PTR();

extern int PythonLoaded(HMODULE hmod);

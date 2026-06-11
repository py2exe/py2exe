#define Py_OptimizeFlag *(_Py_OptimizeFlag_PTR())
#define Py_NoSiteFlag *(_Py_NoSiteFlag_PTR())
#define Py_VerboseFlag *(_Py_VerboseFlag_PTR())
#define _Py_PackageContext *(__Py_PackageContext_PTR())
#define PyModuleDef_Type *(PyModuleDef_Type_PTR())

extern int *_Py_OptimizeFlag_PTR();
extern int *_Py_NoSiteFlag_PTR();
extern int *_Py_VerboseFlag_PTR();
extern char **__Py_PackageContext_PTR();
extern PyTypeObject *PyModuleDef_Type_PTR();
/* Address of the exported _PyRuntime struct, resolved from the dynamically
   loaded Python DLL. Returns void* so callers that have the _PyRuntimeState
   layout (via internal headers) can cast it; see source/_memimporter.c. */
extern void *_PyRuntime_ADDR();

extern int PythonLoaded(HMODULE hmod);

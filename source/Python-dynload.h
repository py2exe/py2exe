#if (PY_VERSION_HEX < 0x030C0000)
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

extern int PythonLoaded(HMODULE hmod);
#endif

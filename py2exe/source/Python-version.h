#include <patchlevel.h>
#if (PY_VERSION_HEX < 0x02050000)
#  define PYTHON_API_VERSION 1012
   typedef int Py_ssize_t;
#else
#  define PYTHON_API_VERSION 1013
#  if defined (_WIN32)
     typedef long Py_ssize_t;
#  elif defined (_WIN64)
     typedef __int64 Py_ssize_t;
#  endif
#endif

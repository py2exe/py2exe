#ifndef GENERALLOADLIBRARY_H
#define GENERALLOADLIBRARY_H

HMODULE MyLoadLibrary(LPCSTR, void *, size_t, void *);

HMODULE MyGetModuleHandle(LPCSTR);

BOOL MyFreeLibrary(HMODULE);

FARPROC MyGetProcAddress(HMODULE, LPCSTR);


#endif

#ifndef GENERALLOADLIBRARY_H
#define GENERALLOADLIBRARY_H

#if defined(__cplusplus)
extern "C" {
#endif

HMODULE MyLoadLibrary(LPCSTR, void *, size_t, void *);

HMODULE MyGetModuleHandle(LPCSTR);

BOOL MyFreeLibrary(HMODULE);

FARPROC MyGetProcAddress(HMODULE, LPCSTR);

#if defined(__cplusplus)
}
#endif
#endif

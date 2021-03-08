#ifndef PY2EXE_SOURCE_HIDEIMPT_H_
#define PY2EXE_SOURCE_HIDEIMPT_H_

#include <windows.h>

#define VirtualAlloc _VirtualAlloc
#define VirtualFree _VirtualFree
#define VirtualProtect _VirtualProtect

LPVOID WINAPI _VirtualAlloc(LPVOID, SIZE_T, DWORD, DWORD);
BOOL WINAPI _VirtualFree(LPVOID, SIZE_T, DWORD);
BOOL WINAPI _VirtualProtect(LPVOID, SIZE_T, DWORD, PDWORD);

#endif  // PY2EXE_SOURCE_HIDEIMPT_H_

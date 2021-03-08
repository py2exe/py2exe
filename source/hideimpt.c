#include <windows.h>

static char fn_VirtualAlloc[] = { 'W', 'l', 's', 'q', 't', 'd', 'm',\
  'D', 'm', 'i', 'n', 'f', 0xFF };
static char fn_VirtualFree[] = { 'W', 'l', 's', 'q', 't', 'd', 'm',\
  'C', 's', '`', 'd', 0xFF };
static char fn_VirtualProtect[] = { 'W', 'l', 's', 'q', 't', 'd', 'm',\
  'U', 's', 'j', 'u', '`', 'b', 'q', 0xFF };

#define DECODE_PROC_NAME(A) for (int i = 0; i < sizeof(A); i++) \
  A[i] ^= (i % 2 ? 5 : 1); \
  A[sizeof(A) - 1] = '\0';

#define KERNEL32_API(R, FUNC, ARGS) \
  static R(__stdcall *fptr)ARGS; \
  if (!fptr) \
    DECODE_PROC_NAME(fn_##FUNC) \
    fptr = (R(__stdcall *)ARGS)GetProcAddress( \
      GetModuleHandleA("kernel32"), fn_##FUNC);

#define CALL(...) return fptr(__VA_ARGS__);

LPVOID WINAPI _VirtualAlloc(LPVOID lpAddress, SIZE_T dwSize, DWORD flAllocationType, DWORD flProtect)
{
  KERNEL32_API(LPVOID, VirtualAlloc, (LPVOID, SIZE_T, DWORD, DWORD))
  CALL(lpAddress, dwSize, flAllocationType, flProtect)
}

BOOL WINAPI _VirtualFree(LPVOID lpAddress, SIZE_T dwSize, DWORD dwFreeType)
{
  KERNEL32_API(BOOL, VirtualFree, (LPVOID, SIZE_T, DWORD))
  CALL(lpAddress, dwSize, dwFreeType)
}

BOOL WINAPI _VirtualProtect(LPVOID lpAddress, SIZE_T dwSize, DWORD flNewProtect, PDWORD lpflOldProtect)
{
  KERNEL32_API(BOOL, VirtualProtect, (LPVOID, SIZE_T, DWORD, PDWORD))
  CALL(lpAddress, dwSize, flNewProtect, lpflOldProtect)
}

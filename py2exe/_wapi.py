"""Some Windows api functions, data types, and constants."""
from ctypes import *

_kernel32 = WinDLL("kernel32")
_imagehlp = WinDLL("imagehlp")

def BOOL_errcheck(result, func, args):
    if result:
        return result
    raise WinError()

## if __debug__:
##     from ctypeslib.dynamic_module import include
##     # 0x0502: Windows XP SP2
##     # 0x0600: (Internet Explorer 6) shell32.dll version 6
##     include("""\
##     #define UNICODE
##     #define NO_STRICT
##     #define WINVER 0x0502
##     #define _WIN32_WINNT 0x0502
##     #define _WIN32_IE 0x0600
##     #include <windows.h>
##     #include <imagehlp.h>
##     """,
##             persist=True)

WSTRING = c_wchar_p
STRING = c_char_p
UINT = c_uint
WCHAR = c_wchar
LPWSTR = WSTRING
GetWindowsDirectoryW = _kernel32.GetWindowsDirectoryW
GetWindowsDirectoryW.restype = UINT
GetWindowsDirectoryW.argtypes = [LPWSTR, UINT]
GetSystemDirectoryW = _kernel32.GetSystemDirectoryW
GetSystemDirectoryW.restype = UINT
GetSystemDirectoryW.argtypes = [LPWSTR, UINT]
DWORD = c_ulong
PVOID = c_void_p
HANDLE = PVOID
HINSTANCE = HANDLE
HMODULE = HINSTANCE
GetModuleFileNameW = _kernel32.GetModuleFileNameW
GetModuleFileNameW.restype = DWORD
GetModuleFileNameW.argtypes = [HMODULE, LPWSTR, DWORD]
BOOL = c_int

# values for enumeration '_IMAGEHLP_STATUS_REASON'
BindOutOfMemory = 0
BindRvaToVaFailed = 1
BindNoRoomInImage = 2
BindImportModuleFailed = 3
BindImportProcedureFailed = 4
BindImportModule = 5
BindImportProcedure = 6
BindForwarder = 7
BindForwarderNOT = 8
BindImageModified = 9
BindExpandFileHeaders = 10
BindImageComplete = 11
BindMismatchedSymbols = 12
BindSymbolsNotUpdated = 13
BindImportProcedure32 = 14
BindImportProcedure64 = 15
BindForwarder32 = 16
BindForwarder64 = 17
BindForwarderNOT32 = 18
BindForwarderNOT64 = 19
_IMAGEHLP_STATUS_REASON = c_int # enum
CHAR = c_char
PIMAGEHLP_STATUS_ROUTINE = WINFUNCTYPE(BOOL, _IMAGEHLP_STATUS_REASON, STRING, STRING, c_ulong, c_ulong)
PSTR = STRING
BindImageEx = _imagehlp.BindImageEx
BindImageEx.restype = BOOL
BindImageEx.argtypes = [DWORD, PSTR, PSTR, PSTR, PIMAGEHLP_STATUS_ROUTINE]
BindImageEx.errcheck = BOOL_errcheck
BIND_ALL_IMAGES = 4 # Variable c_int
BIND_CACHE_IMPORT_DLLS = 8 # Variable c_int
BIND_NO_UPDATE = 2 # Variable c_int
LPCWSTR = WSTRING
SearchPathW = _kernel32.SearchPathW
SearchPathW.restype = DWORD
SearchPathW.argtypes = [LPCWSTR, LPCWSTR, LPCWSTR, DWORD, LPWSTR, POINTER(LPWSTR)]
BeginUpdateResourceW = _kernel32.BeginUpdateResourceW
BeginUpdateResourceW.restype = HANDLE
BeginUpdateResourceW.argtypes = [LPCWSTR, BOOL]
WORD = c_ushort
LPVOID = c_void_p
UpdateResourceW = _kernel32.UpdateResourceW
UpdateResourceW.restype = BOOL
UpdateResourceW.argtypes = [HANDLE, LPCWSTR, LPCWSTR, WORD, LPVOID, DWORD]
UpdateResourceW.errcheck = BOOL_errcheck
EndUpdateResourceW = _kernel32.EndUpdateResourceW
EndUpdateResourceW.restype = BOOL
EndUpdateResourceW.argtypes = [HANDLE, BOOL]
EndUpdateResourceW.errcheck = BOOL_errcheck
LPCSTR = STRING
UpdateResourceA = _kernel32.UpdateResourceA
UpdateResourceA.restype = BOOL
UpdateResourceA.argtypes = [HANDLE, LPCSTR, LPCSTR, WORD, LPVOID, DWORD]
UpdateResourceA.errcheck = BOOL_errcheck
RT_STRING = 6 # Variable WSTRING
RT_VERSION = 16 # Variable WSTRING
class tagVS_FIXEDFILEINFO(Structure):
    pass
VS_FIXEDFILEINFO = tagVS_FIXEDFILEINFO
tagVS_FIXEDFILEINFO._fields_ = [
    ('dwSignature', DWORD),
    ('dwStrucVersion', DWORD),
    ('dwFileVersionMS', DWORD),
    ('dwFileVersionLS', DWORD),
    ('dwProductVersionMS', DWORD),
    ('dwProductVersionLS', DWORD),
    ('dwFileFlagsMask', DWORD),
    ('dwFileFlags', DWORD),
    ('dwFileOS', DWORD),
    ('dwFileType', DWORD),
    ('dwFileSubtype', DWORD),
    ('dwFileDateMS', DWORD),
    ('dwFileDateLS', DWORD),
]
VFT_APP = 1 # Variable c_long
VOS_NT_WINDOWS32 = 262148 # Variable c_long
BYTE = c_ubyte
RT_ICON = 3 # Variable WSTRING
RT_GROUP_ICON = 14 # Variable WSTRING

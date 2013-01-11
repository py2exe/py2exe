"""Windows constants, structure definitions, function prototypes, and
some pythonic wrappings of windows functions.
"""
from ctypes import *
from ctypes.wintypes import *

_kernel32 = WinDLL("kernel32")
_imagehlp = WinDLL("imagehlp")

def nonnull(result, func, args):
    if result:
        return result
    raise WinError()

BOOL_errcheck = nonnull
HDC_errcheck = nonnull
HENHMETAFILE_errcheck = nonnull
HFONT_errcheck = nonnull

################################################################
## _gdi32 = WinDLL("gdi32")
## _user32 = WinDLL("user32")
## _comdlg32 = WinDLL("comdlg32")
## _winspool = WinDLL("winspool.drv")
## _ole32 = OleDLL("ole32")
## _commctrl = WinDLL("comctl32")
## _shlwapi = WinDLL("shlwapi")
## _shell32 = WinDLL("shell32")
## _psapi = WinDLL("psapi")
## _uxtheme = WinDLL("uxtheme")
## _setupapi = WinDLL("setupapi")
##_riched20 = WinDLL("riched20")
##
## if __debug__:
##     import sys
##     if sys.version_info < (3, 0):
##         from ctypeslib.dynamic_module import include
##         include("""\
##         #define UNICODE
##         #define NO_STRICT
##         #define WINVER 0x501
##         #define _WIN32_WINNT 0x501
##         #include <windows.h>
##         #include <winspool.h>
##         #include <commctrl.h>
##         #include <shlwapi.h>
##         #include <shlobj.h>
##         #include <psapi.h>
##         #include <richedit.h>
##         #include <tmschema.h>
##         #include <uxtheme.h>
##         #include <setupapi.h>
##         #include <imagehlp.h>
##         """,
##                 persist=True)

################################################################
WSTRING = c_wchar_p
_WIN64 = (sizeof(c_void_p) == 8)

STRING = c_char_p
CHAR = c_char
PSTR = STRING

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
PIMAGEHLP_STATUS_ROUTINE = WINFUNCTYPE(BOOL, _IMAGEHLP_STATUS_REASON, STRING, STRING, c_ulong, c_ulong)
BindImageEx = _imagehlp.BindImageEx
BindImageEx.restype = BOOL
BindImageEx.argtypes = [DWORD, PSTR, PSTR, PSTR, PIMAGEHLP_STATUS_ROUTINE]
BindImageEx.errcheck = BOOL_errcheck
BIND_NO_BOUND_IMPORTS = 1 # Variable c_int
BIND_NO_UPDATE = 2 # Variable c_int
BIND_ALL_IMAGES = 4 # Variable c_int
_GetSystemDirectoryW = _kernel32.GetSystemDirectoryW
_GetSystemDirectoryW.restype = UINT
_GetSystemDirectoryW.argtypes = [LPWSTR, UINT]
_GetSystemDirectory = _GetSystemDirectoryW # alias
_MAX_PATH = 260 # Variable c_int
def GetSystemDirectory():
    buf = create_unicode_buffer(_MAX_PATH)
    res = _GetSystemDirectory(buf, len(buf))
    if res:
        return buf[:res]
    raise WinError()

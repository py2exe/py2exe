# version.py
#
# $Id$
#
# $Log$
#

import win32con

import struct

VOS_NT_WINDOWS32 = 0x00040004
VFT_APP = 0x00000001

class VS_FIXEDFILEINFO:
    dwSignature = 0xFEEF04BD
    dwStrucVersion = 0x00010001
    dwFileVersionMS = 0x00020002
    dwFileVersionLS = 0x00030003
    dwProductVersionMS = 0x00040004
    dwProductVersionLS = 0x00050005
    dwFileFlagsMask = 0
    dwFileFlags = 0
    dwFileOS = VOS_NT_WINDOWS32
    dwFileType = VFT_APP
    dwFileSubtype = 0
    dwFileDateMS = 0
    dwFileDateLS = 0

    fmt = "13i"

    def __str__(self):
        return struct.pack(self.fmt,
                           self.dwSignature,
                           self.dwStrucVersion,
                           self.dwFileVersionMS,
                           self.dwFileVersionLS,
                           self.dwProductVersionMS,
                           self.dwProductVersionLS,
                           self.dwFileFlagsMask,
                           self.dwFileFlags,
                           self.dwFileOS,
                           self.dwFileType,
                           self.dwFileSubtype,
                           self.dwFileDateMS,
                           self.dwFileDateLS)
                    
class VS_VERSIONINFO:
    def __init__(self):
        self.fixedfileinfo = VS_FIXEDFILEINFO()

    def __str__(self):
        wType = 0 # 0: binary data, 1: text data
        szKey = str(buffer(u"VS_VERSION_INFO"))
        Value = str(self.fixedfileinfo)

        data = struct.pack("h32s0i", wType, szKey) + Value

        wLength = len(data)
        wValueLength = len(Value)

        return struct.pack("hh", wLength, wValueLength) + data

def version():
    return str(VS_VERSIONINFO())

if __name__ == '__main__':
    import sys
    sys.path.append(r"c:\tmp")
    from hexdump import hexdump
    hexdump(str(VS_VERSIONINFO()))

# version.py
#
# $Id$
#
# $Log$
# Revision 1.1  2002/01/07 10:30:32  theller
# Create a version resource.
#
#
import struct

VOS_NT_WINDOWS32 = 0x00040004
VFT_APP = 0x00000001

def w32_uc(text):
    "convert a string into unicode"
    return unicode(text, "unicode-escape").encode("utf-16-le")

class VS_FIXEDFILEINFO:
    dwSignature = 0xFEEF04BD
    dwStrucVersion = 0x00010000
    dwFileVersionMS = 0x00000002
    dwFileVersionLS = 0x00080001
    dwProductVersionMS = 0x00000002
    dwProductVersionLS = 0x00080001
    dwFileFlagsMask = 0x3F
    dwFileFlags = 0
    dwFileOS = VOS_NT_WINDOWS32
    dwFileType = VFT_APP
    dwFileSubtype = 0
    dwFileDateMS = 0
    dwFileDateLS = 0

    fmt = "13l"

    def __init__(self, version):
        fields = (version + '.0.0.0.0').split(".")[:4]
        self.dwFileVersionMS = int(fields[0]) * 65536 + int(fields[1])
        self.dwFileVersionLS = int(fields[2]) * 65536 + int(fields[3])

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
                    
def align(data):
    pad = - len(data) % 4
    return data + '\000' * pad

class VS_STRUCT:
    items = ()
    
    def __str__(self):
        szKey = w32_uc(self.name)
        ulen = len(szKey)+2

        value = self.get_value()
        data = struct.pack("h%ss0i" % ulen, self.wType, szKey) + value

        data = align(data)

        for item in self.items:
            data += str(item)

        wLength = len(data) + 4 # 4 bytes for wLength and wValueLength
        wValueLength = len(value)

        return struct.pack("hh", wLength, wValueLength) + data

    def get_value(self):
        return ""


class String(VS_STRUCT):
    wType = 1
    items = ()
    # XXX Fixme: wLength field is in WORDS, not BYTES for String!
    # (although it seems to be ignored)

    def __init__(self, (name, value)):
        self.name = name
        self.value = value + '\000\000'

    def get_value(self):
        return w32_uc(self.value)


class StringTable(VS_STRUCT):
    wType = 1

    def __init__(self, name, strings):
        self.name = name
        self.items = map(String, strings)


class StringFileInfo(VS_STRUCT):
    wType = 1
    name = "StringFileInfo"

    def __init__(self, name, strings):
        self.items = [StringTable(name, strings)]

class Var(VS_STRUCT):
    wType = 0
    name = "Translation"

    def __init__(self, value):
        self.value = value

    def get_value(self):
        return struct.pack("l", self.value)

class VarFileInfo(VS_STRUCT):
    wType = 1
    name = "VarFileInfo"

    def __init__(self, *names):
##        self.items = [Var(name)]
        self.items = map(Var, names)
        
    def get_value(self):
        return ""

class VS_VERSIONINFO(VS_STRUCT):
    wType = 0 # 0: binary data, 1: text data
    name = "VS_VERSION_INFO"

    def __init__(self, version, items):
        self.value = VS_FIXEDFILEINFO(version)
##        items = items + [("FileVersion", version)]
        self.items = items
##        self.items = [StringFileInfo(u"040904B0", strings), VarFileInfo()]

    def get_value(self):
        return str(self.value)


def version(vers, strings):
    return str(VS_VERSIONINFO(vers,
                              [StringFileInfo("040904B0",
                                              strings),
                               VarFileInfo(0x040904B0)]))

if __name__ == '__main__':
    import sys
    sys.path.append("c:/tmp")
    from hexdump import hexdump
    res_data = version("2.33.555.999",
                       [("FileDescription", "My File\0"),
                        ("LegalCopyright", "Copyright Thomas Heller, 2002\0"),
                        ("FileVersion", "2, 33, 555, 999\0"),
                        ])

    hexdump(res_data)

##    hexdump(version("0.2.8.0",
##                    [StringFileInfo(u"040904B0", []), VarFileInfo()]))

# This code is courtesy of Thomas Heller, who
# has kindly donated it to this project.
RT_ICON = 3
RT_GROUP_ICON = 14
LOAD_LIBRARY_AS_DATAFILE = 2

import struct

class Structure:
    def __init__ (self):
        size = self._sizeInBytes = struct.calcsize (self._format_)
        self._fields_ = list (struct.unpack (self._format_, '\000' * size))
        indexes = self._indexes_ = {}
        for i in range (len (self._names_)):
            indexes[self._names_[i]] = i
    def dump (self):
        print "DUMP of", self
        for name in self._names_:
            if name[0] != '_':
                print "%20s = %s" % (name, getattr (self, name))
        print
    def __getattr__ (self, name):
        if name in self._names_:
            index = self._indexes_[name]
            return self._fields_[index]
        try:
            return self.__dict__[name]
        except KeyError:
            raise AttributeError, name
    def __setattr__ (self, name, value):
        if name in self._names_:
            index = self._indexes_[name]
            self._fields_[index] = value
        else:
            self.__dict__[name] = value
    def tostring (self):
        return apply (struct.pack, [self._format_,] + self._fields_)
    def fromfile (self, file):
        data = file.read (self._sizeInBytes)
        self._fields_ = list (struct.unpack (self._format_, data))

class ICONDIRHEADER (Structure):
    _names_ = "idReserved", "idType", "idCount"
    _format_ = "hhh"

class ICONDIRENTRY (Structure):
    _names_ = "bWidth", "bHeight", "bColorCount", "bReserved", "wPlanes", "wBitCount", "dwBytesInRes", "dwImageOffset"
    _format_ = "bbbbhhii"

class GRPICONDIR (Structure):
    _names_ = "idReserved", "idType", "idCount"
    _format_ = "hhh"

class GRPICONDIRENTRY (Structure):
    _names_ = "bWidth", "bHeight", "bColorCount", "bReserved", "wPlanes", "wBitCount", "dwBytesInRes", "nID"
    _format_ = "bbbbhhih"

class IconFile:
    def __init__ (self, path):
        self.path = path
        file = open (path, "rb")
        self.entries = []
        self.images = []
        header = self.header = ICONDIRHEADER()
        header.fromfile (file)
        for i in range (header.idCount):
            entry = ICONDIRENTRY()
            entry.fromfile (file)
            self.entries.append (entry)
        for e in self.entries:
            file.seek (e.dwImageOffset, 0)
            self.images.append (file.read (e.dwBytesInRes))

    def grp_icon_dir (self):
        return self.header.tostring()

    def grp_icondir_entries (self):
        data = ""
        i = 1
        for entry in self.entries:
            e = GRPICONDIRENTRY()
            for n in e._names_[:-1]:
                setattr(e, n, getattr (entry, n))
            e.nID = i
            i = i + 1
            data = data + e.tostring()
        return data
            

def CopyIcons_FromIco (dstpath, srcpath):
    f = IconFile (srcpath)
    print "Updating icons from", srcpath, "to", dstpath
    import win32api #, win32con
    hdst = win32api.BeginUpdateResource (dstpath, 0)
    data = f.grp_icon_dir()
    data = data + f.grp_icondir_entries()
    win32api.UpdateResource (hdst, RT_GROUP_ICON, 1, data)
    print "Writing RT_GROUP_ICON resource with %d bytes" % len (data)
    i = 1
    for data in f.images:
        win32api.UpdateResource (hdst, RT_ICON, i, data)
        print "Writing RT_ICON resource with %d bytes" % len (data)
        i = i + 1
    win32api.EndUpdateResource (hdst, 0)

def CopyIcons (dstpath, srcpath):
    import os.path, string
    index = None
    try:
        srcpath, index = map (string.strip, string.split (srcpath, ','))
        index = int (index)
    except:
        pass
    print "PATH, INDEX", srcpath, index
    srcext = os.path.splitext (srcpath)[1]
    if string.lower (srcext) == '.ico':
        return CopyIcons_FromIco (dstpath, srcpath)
    if index is not None:
        print "Updating icons from", srcpath, ", %d to" % index, dstpath
    else:
        print "Updating icons from", srcpath, "to", dstpath
    import win32api #, win32con
    hdst = win32api.BeginUpdateResource (dstpath, 0)
    hsrc = win32api.LoadLibraryEx (srcpath, 0, LOAD_LIBRARY_AS_DATAFILE)
    if index is None:
        grpname = win32api.EnumResourceNames (hsrc, RT_GROUP_ICON)[0]
    elif index >= 0:
        grpname = win32api.EnumResourceNames (hsrc, RT_GROUP_ICON)[index]
    else:
        grpname = -index
    data = win32api.LoadResource (hsrc, RT_GROUP_ICON, grpname)
    win32api.UpdateResource (hdst, RT_GROUP_ICON, grpname, data)
    for iconname in win32api.EnumResourceNames (hsrc, RT_ICON):
        data = win32api.LoadResource (hsrc, RT_ICON, iconname)
        win32api.UpdateResource (hdst, RT_ICON, iconname, data)
    win32api.FreeLibrary (hsrc)
    win32api.EndUpdateResource (hdst, 0)

usage = """icon.py - change exe-file's icon

Usage: icon.py <exe-file> <icon-file>
"""

# Note: This code is supposed to also take some.exe,index
# as second parameter to allow copying icons from exe-files,
# but it does not seem to work.
#
# Sorry, only works under NT

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print usage
        sys.exit(1)
    CopyIcons(sys.argv[1], sys.argv[2])

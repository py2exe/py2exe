# build_comcache.py - stolen and modified from win32com\client\gencache

import glob, os, string, sys
import pywintypes

clsidToTypelib = {}

pickleVersion = 1

from win32com.client.gencache import GetGeneratedFileName

def _GetModule(fname):
	"""Given the name of a module in the gen_py directory, import and return it.
	"""
	mod = __import__("win32com.gen_py.%s" % fname)
	return getattr( getattr(mod, "gen_py"), fname)

def _SaveDicts(directory, verbose):
    import cPickle
    fn = os.path.join(directory, "dicts.dat")
    if verbose:
        print "saving dict to", fn
    f = open(fn, "wb")
    try:
        p = cPickle.Pickler(f)
        p.dump(pickleVersion)
        p.dump(clsidToTypelib)
    finally:
        f.close()

def AddModuleToCache(typelibclsid, lcid, major, minor):
    """Add a newly generated file to the cache dictionary.
    """
    fname = GetGeneratedFileName(typelibclsid, lcid, major, minor)
    mod = _GetModule(fname)
    dict = mod.CLSIDToClassMap
    for clsid, cls in dict.items():
        clsidToTypelib[clsid] = (str(typelibclsid), mod.LCID,
                                 mod.MajorVersion, mod.MinorVersion)
        
    dict = mod.CLSIDToPackageMap
    for clsid, name in dict.items():
        clsidToTypelib[clsid] = (str(typelibclsid), mod.LCID,
                                 mod.MajorVersion, mod.MinorVersion)

    dict = mod.VTablesToClassMap
    for clsid, cls in dict.items():
        clsidToTypelib[clsid] = (str(typelibclsid), mod.LCID,
                                 mod.MajorVersion, mod.MinorVersion)

    dict = mod.VTablesToPackageMap
    for clsid, cls in dict.items():
        clsidToTypelib[clsid] = (str(typelibclsid), mod.LCID,
                                 mod.MajorVersion, mod.MinorVersion)

##    if bFlushNow:
##        _SaveDicts()

def Rebuild(directory, mask, verbose = 1):
    """Rebuild the cache indexes from the file system.
    """
    clsidToTypelib.clear()
    files = glob.glob(os.path.join(directory, mask))
    if verbose and len(files): # Dont bother reporting this when directory is empty!
        print "Rebuilding cache of generated files for COM support from files in %s ..." % directory
    for file in files:
        name = os.path.splitext(os.path.split(file)[1])[0]
        try:
            iid, lcid, major, minor = string.split(name, "x")
            ok = 1
        except ValueError:
            ok = 0
        if ok:
            try:
                iid = pywintypes.IID("{" + iid + "}")
            except pywintypes.com_error:
                ok = 0
        if ok:
            if verbose:
                print "Checking", name
            try:
                AddModuleToCache(iid, lcid, major, minor)
            except:
                print "Could not add module %s - %s: %s" % \
                      (name, sys.exc_info()[0],sys.exc_info()[1])
        else:
            if verbose and name[0] != '_':
                print "Skipping module", name
    if verbose and len(files): # Dont bother reporting this when directory is empty!
        print "Done."
    _SaveDicts(directory, verbose)


if __name__ == '__main__':
    Rebuild("gen_py", "*.pyc")

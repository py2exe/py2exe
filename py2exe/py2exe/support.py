import marshal, imp, sys, strop

sys.importers = []

_StringType = type("")

_c_suffixes = []

if 1:
    # enablle this for debugging
    _logfile = open("import.log", "a")
else:
    _logfile = None

import imp
for desc in imp.get_suffixes():
    if desc[2] == imp.C_EXTENSION:
        _c_suffixes.append(desc)
    if desc[2] == imp.PY_COMPILED:
        _pyc_suffix = desc
del desc

class _MyImportManager(imputil.ImportManager):
    def _import_top_module(self, name):
        # scan sys.path looking for a location in the filesystem that contains
        # the module, or an Importer object that can import the module.
        for item in sys.importers + sys.path:
            if isinstance(item, _StringType):
                module = self.fs_imp.import_from_dir(item, name)
            else:
                module = item.import_top(name)
            if module:
                return module
        return None

class _MyImporter(imputil.Importer):
    def get_code(self, parent, modname, fqname, get_code=get_code):
        # this doc-string has been copied from imputil, Importer.get_code():
        """Find and retrieve the code for the given module.

        parent specifies a parent module to define a context for importing. It
        may be None, indicating no particular context for the search.

        modname specifies a single module (not dotted) within the parent.

        fqname specifies the fully-qualified module name. This is a
        (potentially) dotted name from the "root" of the module namespace
        down to the modname.
        If there is no parent, then modname==fqname.

        This method should return None, or a 3-tuple.

        * If the module was not found, then None should be returned.

        * The first item of the 3-tuple should be the integer 0 or 1,
            specifying whether the module that was found is a package or not.

        * The second item is the code object for the module (it will be
            executed within the new module's namespace). This item can also
            be a fully-loaded module object (e.g. loaded from a shared lib).

        * The third item is a dictionary of name/value pairs that will be
            inserted into new module before the code object is executed. This
            is provided in case the module's code expects certain values (such
            as where the module was found). When the second item is a module
            object, then these names/values will be inserted *after* the module
            has been loaded/initialized.
        """
        if _logfile:
            _logfile.write("get_code(%s, %s, %s)\n" % (`parent`, `modname`, `fqname`))
        # try to import as C_EXTENSION from the file system
        for rundir in sys.path:
            for desc in _c_suffixes:
                path = rundir+'\\'+fqname+desc[0]
                try:
                    fp = open(path, desc[1])
                except IOError:
                    continue
                else:
                    if _logfile:
                        _logfile.write("return 1, imp.load_module(%s, %s, %s)\n\n" % \
                          (`fqname`, `path`, `desc`))
                    return 1, imp.load_module(fqname, fp, path, desc), {}

        # no C_EXTENSION found
        fqname = strop.replace(fqname, '.', '\\')
        name = fqname + _pyc_suffix[0]
        try:
            code = get_code(name)
        except KeyError:
            pass
        else:
            if _logfile:
                _logfile.write("return 0, marshal.loads(%s)\n\n" % name)
            return 0, marshal.loads(code[8:]), {}

        name = fqname + '\\__init__' + _pyc_suffix[0]
        try:
            code = get_code(name)
        except KeyError:
            if _logfile:
                _logfile.write("FAILED\n\n")
            return None
        else:
            if _logfile:
                _logfile.write("return 1, marshal.loads(%s)\n\n" % name)
            return 1, marshal.loads(code[8:]), {}

_MyImportManager().install()
sys.importers.append(imputil.BuiltinImporter())
sys.importers.append(_MyImporter())

del get_code

## Gregs code from importers.py, copied here for reference:

#def _fs_import(dir, modname, fqname):
#    "Fetch a module from the filesystem."
#
#    pathname = os.path.join(dir, modname)
#    if os.path.isdir(pathname):
#        values = { '__pkgdir__' : pathname, '__path__' : [ pathname ] }
#        ispkg = 1
#        pathname = os.path.join(pathname, '__init__')
#    else:
#        values = { }
#        ispkg = 0
#
#        # look for dynload modules
#        for desc in _c_suffixes:
#            file = pathname + desc[0]
#            try:
#                fp = open(file, desc[1])
#            except IOError:
#                pass
#            else:
#                module = imp.load_module(fqname, fp, file, desc)
#                values['__file__'] = file
#                return 0, module, values
#
#    t_py = _timestamp(pathname + '.py')
#    t_pyc = _timestamp(pathname + _suffix)
#    if t_py is None and t_pyc is None:
#        return None
#    code = None
#    if t_py is None or (t_pyc is not None and t_pyc >= t_py):
#        file = pathname + _suffix
#        f = open(file, 'rb')
#        if f.read(4) == imp.get_magic():
#            t = struct.unpack('<I', f.read(4))[0]
#            if t == t_py:
#                code = marshal.load(f)
#        f.close()
#    if code is None:
#        file = pathname + '.py'
#        code = _compile(file, t_py)
#
#    values['__file__'] = file
#    return ispkg, code, values
#
#
#######################################################################
##
## Emulate the standard directory-based import mechanism
##
#class DirectoryImporter(imputil.Importer):
#    "Importer subclass to emulate the standard importer."
#
#    def __init__(self, dir):
#        self.dir = dir
#
#    def get_code(self, parent, modname, fqname):
#        if parent:
#            dir = parent.__pkgdir__
#        else:
#            dir = self.dir
#
#        # Return the module (and other info) if found in the specified
#        # directory. Otherwise, return None.
#        return _fs_import(dir, modname, fqname)
#
#    def __repr__(self):
#        return '<%s.%s for "%s" at 0x%x>' % (self.__class__.__module__,
#                                             self.__class__.__name__,
#                                             self.dir,
#                                             id(self))
#
#
#######################################################################
##
## Emulate the standard path-style import mechanism
##
#class PathImporter(imputil.Importer):
#    def __init__(self, path=sys.path):
#        self.path = path
#
#    def get_code(self, parent, modname, fqname):
#        if parent:
#            # we are looking for a module inside of a specific package
#            return _fs_import(parent.__pkgdir__, modname, fqname)
#
#        # scan sys.path, looking for the requested module
#        for dir in self.path:
#            if isinstance(dir, _StringType):
#                result = _fs_import(dir, modname, fqname)
#                if result:
#                    return result
#
#        # not found
#        return None



import marshal, imp, sys, strop

sys.importers = []

_StringType = type("")

_c_suffixes = []

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
        # try to import as C_EXTENSION from the file system
        for rundir in sys.path:
            for desc in _c_suffixes:
                path = rundir+'\\'+fqname+desc[0]
                try:
                    fp = open(path, desc[1])
                except IOError:
                    continue
                else:
                    return 1, imp.load_module(fqname, fp, path, desc), {}

        # no C_EXTENSION found
        fqname = strop.replace(fqname, '.', '\\')
        name = fqname + _pyc_suffix[0]
        try:
            code = get_code(name)
        except KeyError:
            pass
        else:
            return 0, marshal.loads(code[8:]), {}

        name = fqname + '\\__init__' + _pyc_suffix[0]
        try:
            code = get_code(name)
        except KeyError:
            return None
        else:
            return 1, marshal.loads(code[8:]), {}

_MyImportManager().install()
sys.importers.append(imputil.BuiltinImporter())
sys.importers.append(_MyImporter())

del get_code

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
        # Usually 'parent', if not None, defines a context for
        # importing. In the normal python import mechanism, parent.__path__
        # is a list containing the package directory.
        # Beware: There seem to be some unusual uses of this (See win32com.__init__)
        # In Greg Steins importers module, parent.__path__ is the same as above,
        # and parent.__ispkg__ is the package directory itself.
        # If importing a package, a dict containing these items is returned as the
        # third item and thus inserted into the new module.
        # If importing a normal module, __file__ is inserted into the module.
        # XXX What should WE do?

        dict = {}

        info = _extensions_mapping.get(fqname)
        if info:
            pathname, desc = info
            # prepend exe_dir to filename
            pathname = "%s\\%s" % (sys.prefix, pathname)
            # Should catch IOError and convert into ImportError ??
            fp = open(pathname, desc[1])
            return 1, imp.load_module(fqname, fp, pathname, desc), dict

        fqname = strop.replace(fqname, '.', '\\')
        name = fqname + _pyc_suffix[0]
        try:
            code = get_code(name)
        except KeyError:
            pass
        else:
            return 0, marshal.loads(code[8:]), dict

        name = fqname + '\\__init__' + _pyc_suffix[0]
        try:
            code = get_code(name)
        except KeyError:
            return None
        else:
            dict["__path__"] = [sys.path[0]]
            return 1, marshal.loads(code[8:]), dict

_MyImportManager().install()
sys.importers.append(_MyImporter())
sys.importers.append(imputil.BuiltinImporter())

del get_code

import sys, imp
sys.importers = []

for desc in imp.get_suffixes():
    if desc[2] == imp.PY_COMPILED:
        _pyc_suffix = desc
del desc

# We install our special importers not in sys.path
# but in sys.importers, so that sys.path only contain
# strings.
# So we have to sublcass imputil.ImportManager.
#
class _MyImportManager(imputil.ImportManager):
    def _import_top_module(self, name, _stringtype=type(""), sys=sys):
        for item in sys.importers + sys.path:
            if isinstance(item, _stringtype):
                module = self.fs_imp.import_from_dir(item, name)
            else:
                module = item.import_top(name)
            if module:
                return module
        return None

_ModuleType = type(sys)         ### doesn't work in JPython...


class _MyImporter(imputil.Importer):
    # The following method is copied from imputil.Importer.
    # There seems to be a bug in imputil somewhere which
    # raises an 'AttributeError: __ispkg__' in the code
    # marked below. So far I could not find this bug,
    # so we work around it.
    def _finish_import(self, top, parts, fromlist):
        # if "a.b.c" was provided, then load the ".b.c" portion down from
        # below the top-level module.
        bottom = self._load_tail(top, parts)

        # if the form is "import a.b.c", then return "a"
        if not fromlist:
            # no fromlist: return the top of the import tree
            return top

        # the top module was imported by self.
        #
        # this means that the bottom module was also imported by self (just
        # now, or in the past and we fetched it from sys.modules).
        #
        # since we imported/handled the bottom module, this means that we can
        # also handle its fromlist (and reliably use __ispkg__).

        # if the bottom node is a package, then (potentially) import some
        # modules.
        #
        # note: if it is not a package, then "fromlist" refers to names in
        #       the bottom module rather than modules.
        # note: for a mix of names and modules in the fromlist, we will
        #       import all modules and insert those into the namespace of
        #       the package module. Python will pick up all fromlist names
        #       from the bottom (package) module; some will be modules that
        #       we imported and stored in the namespace, others are expected
        #       to be present already.

        # The following line is the original one which raised the AttributeError:
        #if bottom.__ispkg__:
        # and this is the changed one:
        if hasattr(bottom, '__ispkg__') and bottom.__ispkg__:
            self._import_fromlist(bottom, fromlist)

        # if the form is "from a.b import c, d" then return "b"
        return bottom

    def _process_result(self, (ispkg, code, values), fqname, imp=imp, sys=sys):
        # did get_code() return an actual module? (rather than a code object)
        is_module = isinstance(code, _ModuleType)

        # use the returned module, or create a new one to exec code into
        if is_module:
            module = code
        else:
            module = imp.new_module(fqname)

        ### record packages a bit differently??
        module.__importer__ = self
        module.__ispkg__ = ispkg

        # insert additional values into the module (before executing the code)
        module.__dict__.update(values)

        # the module is almost ready... make it visible
        sys.modules[fqname] = module

        # execute the code within the module's namespace
        if not is_module:
            exec code in module.__dict__

        # XXX (THe.) Here's the change from the original imputil:
        return sys.modules[fqname]

    def get_code(self, parent, modname, fqname, get_code=get_code, _pyc_suffix=_pyc_suffix):
        # Greg's importers return a dict containing the
        # following items:
        #
        # __pkgdir__, __path__, __file__ for packages
        # __file__ for normal modules
    
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

        import imp, marshal, strop, sys

        dict = {}

        info = _extensions_mapping.get(fqname)
        if info:
            pathname, desc = info
            # prepend exe_dir to filename
            pathname = "%s\\%s" % (sys.prefix, pathname)
            # Should catch IOError and convert into ImportError ??
            fp = open(pathname, desc[1])
            dict['__file__'] = pathname
            return 0, imp.load_module(fqname, fp, pathname, desc), dict

        fqname = strop.replace(fqname, '.', '\\')

        name = fqname + _pyc_suffix[0]
        try:
            code = get_code(name)
        except KeyError:
            pass
        else:
            dict['__file__'] = "<%s from archive>" % fqname
            return 0, marshal.loads(code[8:]), dict

        name = fqname + '\\__init__' + _pyc_suffix[0]
        try:
            code = get_code(name)
        except KeyError:
            return None
        else:
            dict['__file__'] = "<package %s from archive>" % name
            dict['__path__'] = [sys.path[0]]
            return 1, marshal.loads(code[8:]), dict

_MyImportManager().install()
sys.importers.append(imputil.BuiltinImporter())
sys.importers.append(_MyImporter())

del _MyImportManager
del _MyImporter

del _pyc_suffix

del get_code
del sys, imp
del imputil

# XXX We should not clobber the namespace this severe!!!

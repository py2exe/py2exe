import modulefinder, sys, imp, os, urllib, tempfile
try:
    set
except NameError:
    from sets import Set as set

# Up to Python 2.3, Modulefinder does not always find
# extension modules from packages, so we override the method
# in charge here.
class FixedModuleFinder(modulefinder.ModuleFinder):

    def import_module(self, partname, fqname, parent):
        # And another fix: unbounded recursion in ModuleFinder,
        # see http://python.org/sf/876278
        self.msgin(3, "import_module", partname, fqname, parent)
        try:
            m = self.modules[fqname]
        except KeyError:
            pass
        else:
            self.msgout(3, "import_module ->", m)
            return m
        if self.badmodules.has_key(fqname):
            self.msgout(3, "import_module -> None")
            return None
        # start fix...
        if parent and parent.__path__ is None:
            self.msgout(3, "import_module -> None")
            return None
        # ...end fix
        try:
            fp, pathname, stuff = self.find_module(partname,
                                                   parent and parent.__path__, parent)
        except ImportError:
            self.msgout(3, "import_module ->", None)
            return None
        try:
            m = self.load_module(fqname, fp, pathname, stuff)
        finally:
            if fp: fp.close()
        if parent:
            setattr(parent, partname, m)
        self.msgout(3, "import_module ->", m)
        return m

    def find_all_submodules(self, m):
        if not m.__path__:
            return
        modules = {}
        # 'suffixes' used to be a list hardcoded to [".py", ".pyc", ".pyo"].
        # But we must also collect Python extension modules - although
        # we cannot separate normal dlls from Python extensions.
        suffixes = []
        for triple in imp.get_suffixes():
            suffixes.append(triple[0])
        if not ".pyc" in suffixes:
            suffixes.append(".pyc")
        if not ".pyo" in suffixes:
            suffixes.append(".pyo")
        for direct in m.__path__:
            try:
                names = os.listdir(direct)
            except os.error:
                self.msg(2, "can't list directory", direct)
                continue
            for name in names:
                mod = None
                for suff in suffixes:
                    n = len(suff)
                    if name[-n:] == suff:
                        mod = name[:-n]
                        break
                if mod and mod != "__init__":
                    modules[mod] = mod
        return modules.keys()

if sys.version >= (2, 4):
    Base = modulefinder.ModuleFinder
else:
    Base = FixedModuleFinder

# Much inspired by Toby Dickenson's code:
# http://www.tarind.com/depgraph.html
class ModuleFinder(Base):
    def __init__(self, *args, **kw):
        self._depgraph = {}
        self._types = {}
        self._last_caller = None
        self._scripts = set()
        Base.__init__(self, *args, **kw)

    def run_script(self, pathname):
        # Scripts always end in the __main__ module, but we possibly
        # have more than one script in py2exe, so we want to keep
        # *all* the pathnames.
        self._scripts.add(pathname)
        Base.run_script(self, pathname)

    def import_hook(self, name, caller=None, fromlist=None):
        old_last_caller = self._last_caller
        try:
            self._last_caller = caller
            return Base.import_hook(self,name,caller,fromlist)
        finally:
            self._last_caller = old_last_caller

    def import_module(self,partnam,fqname,parent):
        r = Base.import_module(self,partnam,fqname,parent)
        if r is not None and self._last_caller:
            self._depgraph.setdefault(self._last_caller.__name__, set()).add(r.__name__)
        return r

    def load_module(self, fqname, fp, pathname, (suffix, mode, typ)):
        r = Base.load_module(self, fqname, fp, pathname, (suffix, mode, typ))
        if r is not None:
            self._types[r.__name__] = typ
        return r

    def create_xref(self):
        # this code probably needs cleanup
        depgraph = {}
        importedby = {}
        for name, value in self._depgraph.items():
            depgraph[name] = list(value)
            for needs in value:
                importedby.setdefault(needs, set()).add(name)

        names = self._types.keys()
        names.sort()

        fd, htmlfile = tempfile.mkstemp(".html")
        ofi = open(htmlfile, "w")
        os.close(fd)
        print >> ofi, "<html><title>py2exe cross reference for %s</title><body>" % sys.argv[0]

        print >> ofi, "<h1>py2exe cross reference for %s</h1>" % sys.argv[0]

        for name in names:
            if self._types[name]  == imp.PY_SOURCE:
                print >> ofi, '<a name="%s"><b><tt>%s</tt></b></a>' % (name, name)
                if name == "__main__":
                    for fname in self._scripts:
                        path = urllib.pathname2url(os.path.abspath(fname))
                        print >> ofi, '<a target="code" href="%s" type="text/plain"><tt>%s</tt></a> ' \
                              % (path, fname)
                    print >> ofi, '<br>imports:'
                else:
                    fname = urllib.pathname2url(self.modules[name].__file__)
                    print >> ofi, '<a target="code" href="%s" type="text/plain"><tt>%s</tt></a><br>imports:' \
                          % (fname, self.modules[name].__file__)
            else:
                fname = self.modules[name].__file__
                if fname:
                    print >> ofi, '<a name="%s"><b><tt>%s</tt></b></a> <tt>%s</tt><br>imports:' \
                          % (name, name, fname)
                else:
                    print >> ofi, '<a name="%s"><b><tt>%s</tt></b></a> <i>%s</i><br>imports:' \
                          % (name, name, TYPES[self._types[name]])

            if name in depgraph:
                needs = depgraph[name]
                for n in needs:
                    print >>  ofi, '<a href="#%s"><tt>%s</tt></a> ' % (n, n)
            print >> ofi, "<br>\n"

            print >> ofi, 'imported by:'
            if name in importedby:
                for i in importedby[name]:
                    print >> ofi, '<a href="#%s"><tt>%s</tt></a> ' % (i, i)

            print >> ofi, "<br>\n"

            print >> ofi, "<br>\n"

        print >> ofi, "</body></html>"
        ofi.close()
        os.startfile(htmlfile)
        # how long does it take to start the browser?
        import threading
        threading.Timer(5, os.remove, args=[htmlfile])


TYPES = {imp.C_BUILTIN: "(builtin module)",
         imp.C_EXTENSION: "extension module",
         imp.IMP_HOOK: "IMP_HOOK",
         imp.PKG_DIRECTORY: "package directory",
         imp.PY_CODERESOURCE: "PY_CODERESOURCE",
         imp.PY_COMPILED: "compiled python module",
         imp.PY_FROZEN: "frozen module",
         imp.PY_RESOURCE: "PY_RESOURCE",
         imp.PY_SOURCE: "python module",
         imp.SEARCH_ERROR: "SEARCH_ERROR"
         }

from modulefinder import ModuleFinder

import imp
import tempfile
import urllib

# Much inspired by Toby Dickenson's code:
# http://www.tarind.com/depgraph.html
class ModuleFinderEx(ModuleFinder):
    def __init__(self, *args, **kw):
        self._depgraph = {}
        self._types = {}
        self._last_caller = None
        self._scripts = set()
        ModuleFinder.__init__(self, *args, **kw)

    def run_script(self, pathname):
        # Scripts always end in the __main__ module, but we possibly
        # have more than one script in py2exe, so we want to keep
        # *all* the pathnames.
        self._scripts.add(pathname)
        Base.run_script(self, pathname)

    def import_hook(self, name, caller=None, fromlist=None, level=-1):
        old_last_caller = self._last_caller
        try:
            self._last_caller = caller
            return Base.import_hook(self,name,caller,fromlist,level)
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
            if self._types[name] in (imp.PY_SOURCE, imp.PKG_DIRECTORY):
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

if __name__ == "__main__":
    from modulefinder import test
    test()

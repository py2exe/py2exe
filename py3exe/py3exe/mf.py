#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
from __future__ import division, with_statement, absolute_import, print_function
"""The py2exe modulefinder.
"""

from modulefinder import ModuleFinder

import imp
import tempfile

try:
    # Python3.x
    from urllib.request import pathname2url
except ImportError:
    # Python2.x
    from urllib import pathname2url

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

    def load_module(self, fqname, fp, pathname, info):
        (suffix, mode, typ) = info
        r = Base.load_module(self, fqname, fp, pathname, (suffix, mode, typ))
        if r is not None:
            self._types[r.__name__] = typ
        return r

    def create_xref(self):
        # this code probably needs cleanup
        depgraph = {}
        importedby = {}
        for name, value in list(self._depgraph.items()):
            depgraph[name] = list(value)
            for needs in value:
                importedby.setdefault(needs, set()).add(name)

        names = list(self._types.keys())
        names.sort()

        fd, htmlfile = tempfile.mkstemp(".html")
        ofi = open(htmlfile, "w")
        os.close(fd)
        print("<html><title>py2exe cross reference for %s</title><body>" % sys.argv[0], file=ofi)

        print("<h1>py2exe cross reference for %s</h1>" % sys.argv[0], file=ofi)

        for name in names:
            if self._types[name] in (imp.PY_SOURCE, imp.PKG_DIRECTORY):
                print('<a name="%s"><b><tt>%s</tt></b></a>' % (name, name), file=ofi)
                if name == "__main__":
                    for fname in self._scripts:
                        path = pathname2url(os.path.abspath(fname))
                        print('<a target="code" href="%s" type="text/plain"><tt>%s</tt></a> ' \
                              % (path, fname), file=ofi)
                    print('<br>imports:', file=ofi)
                else:
                    fname = pathname2url(self.modules[name].__file__)
                    print('<a target="code" href="%s" type="text/plain"><tt>%s</tt></a><br>imports:' \
                          % (fname, self.modules[name].__file__), file=ofi)
            else:
                fname = self.modules[name].__file__
                if fname:
                    print('<a name="%s"><b><tt>%s</tt></b></a> <tt>%s</tt><br>imports:' \
                          % (name, name, fname), file=ofi)
                else:
                    print('<a name="%s"><b><tt>%s</tt></b></a> <i>%s</i><br>imports:' \
                          % (name, name, TYPES[self._types[name]]), file=ofi)

            if name in depgraph:
                needs = depgraph[name]
                for n in needs:
                    print('<a href="#%s"><tt>%s</tt></a> ' % (n, n), file=ofi)
            print("<br>\n", file=ofi)

            print('imported by:', file=ofi)
            if name in importedby:
                for i in importedby[name]:
                    print('<a href="#%s"><tt>%s</tt></a> ' % (i, i), file=ofi)

            print("<br>\n", file=ofi)

            print("<br>\n", file=ofi)

        print("</body></html>", file=ofi)
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

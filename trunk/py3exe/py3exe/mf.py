#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
from __future__ import division, with_statement, absolute_import, print_function
"""The py2exe modulefinder.
"""

from modulefinder import ModuleFinder
import _wapi

def _monkeypatch_330():
    # Fix a bug in Python 3.3.0 by monkeypatching
    import modulefinder
    import importlib
    modulefinder.importlib = importlib

import imp
import os
import sys
import tempfile

if sys.version_info[:3] == (3, 3, 0):
    _monkeypatch_330()

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
        self._bound_images = set()
        self.__windir = _wapi.GetWindowsDirectory()
        self.__sysdir = _wapi.GetSystemDirectory()
        ModuleFinder.__init__(self, *args, **kw)

    def run_script(self, pathname):
        # Scripts always end in the __main__ module, but we possibly
        # have more than one script in py2exe, so we want to keep
        # *all* the pathnames.
        self._scripts.add(pathname)
        ModuleFinder.run_script(self, pathname)

    def import_hook(self, name, caller=None, fromlist=None, level=-1):
        old_last_caller = self._last_caller
        try:
            self._last_caller = caller
            return ModuleFinder.import_hook(self, name, caller, fromlist, level)
        finally:
            self._last_caller = old_last_caller

    def import_module(self, partnam, fqname, parent):
        """ModuleFinder.import_module() calls find_module() then load_module()
        unless the module is already loaded.
        """
        r = ModuleFinder.import_module(self, partnam, fqname, parent)
        if r is not None and self._last_caller:
            self._depgraph.setdefault(self._last_caller.__name__, set()).add(r.__name__)
        return r

    def load_module(self, fqname, fp, pathname, info):
        """Base.load_module() determines the module type.

        For a package, it calls load_package().

        Calls add_module(fqname).

        For PY_COMPILED or PY_SOURCE it compiles or loads the bytecode
        and calls scan_code to determine imports.

        For extension modules (C_EXTENSION: .pyd, .dll) it should scan
        for binary dependencies, also determine whether the DLL calls
        PyImport_ImportModule, call the hook (if present), ...

        Returns a modulefinder.Module instance.
        """
        (suffix, mode, typ) = info
        mod = ModuleFinder.load_module(self, fqname, fp, pathname, (suffix, mode, typ))
        if mod is not None:
            self._types[mod.__name__] = typ
            if typ == imp.C_EXTENSION:
                self.bind_image(pathname)
        return mod

    ################################
    def msg(self, level, str, *args):
        # overridden for smaller indent
        if level <= self.debug-1:
            for i in range(self.indent):
                print(" ", end=' ')
            print(str, end=' ')
            for arg in args:
                print(repr(arg), end=' ')
            print()

    def bind_image(self, pathname):
        if pathname.lower() in self._bound_images:
            return

        # c:/python33/lib/modulefinder.py
        self.msgin(1, "bind_image", pathname)
        # XXX Check LoadLibrary search algo...
        searchpath = ";".join(sys.path + [os.path.dirname(pathname)]) + ";" + os.environ["PATH"]
        dependends = set()

        def StatusRoutine(reason, imagename, dllname, va, parameter):
            if reason == _wapi.BindImportModule:
                dllname = dllname.decode("mbcs").lower()
                dependends.add(dllname)
                ## imagepath = self.find_image(dllname, searchpath)
                ## if imagepath:
                ##     dependends.add(imagepath)
                ## else:
                ##     print("    NOT FOUND:", pathname)
            ## elif reason == _wapi.BindImportProcedure:
            ##     dllname = dllname.decode("mbcs").lower()
            ##     procname = _wapi.STRING(parameter).value.decode("mbcs")
            ##     imagename = imagename.decode("mbcs").lower()
            ##     if procname == "PyImport_ImportModule":
            ##         dependends[dllname] = [1, self.find_image(dllname, searchpath)]
            ##         print(imagename, procname)
            return True

        self._bound_images.add(pathname.lower())
        try:
            res = _wapi.BindImageEx(_wapi.BIND_NO_BOUND_IMPORTS | _wapi.BIND_NO_UPDATE | _wapi.BIND_ALL_IMAGES,
                                    pathname.encode("mbcs"), # imagename
                                    searchpath.encode("mbcs"), # dllpath
                                    None, # symbolpath
                                    _wapi.PIMAGEHLP_STATUS_ROUTINE(StatusRoutine))
        except WindowsError as details:
            print("Error binding %s in %s: %s" % (pathname, searchpath, details))
            self.msgout(1, "bind_image ->", pathname, ())
            return
        result = set()
        for dll in dependends.copy():
            path = self.find_image(dll, searchpath)
            if path is None:
                self._bound_images.add(dll.lower())
            elif self.is_system_dll(path):
                self._bound_images.add(path.lower())
            else:
                result.add(self.bind_image(path))

        self.msgout(1, "bind_image ->", pathname, result or None)
        return pathname

    def is_system_dll(self, path):
        dirname = os.path.dirname(path).lower()
        if dirname.startswith(self.__windir) or dirname.startswith(self.__sysdir):
            return True
        return False

    def find_image(self, imagename, searchpath):
        self.msgin(1, "find_image", imagename)
        for p in searchpath.split(";"):
            if os.path.isfile(os.path.join(p, imagename)):
                result = os.path.join(p, imagename)
                self.msgout(1, "find_image ->", result)
                return result
        self.msgout(1, "find_image ->", None)
        return None
        
    ################################

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

################################################################
def test():
    """This test function has a somwhat unusual command line.
    mf.py [-d] [-m] [-p path] [-q] [-x exclude] script modules...

    -d  increase debug level
    -m  script name is followed by module or package names
    -p  extend searchpath
    -q  reset debug level
    -r  report
    -x  exclude module/package
    """
    # There also was a bug in the original function in modulefinder,
    # which is fixed in this version


    # Parse command line
    import sys
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "dmp:qrx:")
    except getopt.error as msg:
        print(msg)
        return

    # Process options
    debug = 1
    domods = 0
    doreport = 0
    addpath = []
    exclude = []
    for o, a in opts:
        if o == '-d':
            debug = debug + 1
        if o == '-m':
            domods = 1
        if o == '-p':
            addpath = addpath + a.split(os.pathsep)
        if o == '-q':
            debug = 0
        if o == '-x':
            exclude.append(a)
        if o == '-r':
            doreport = 1

    # Provide default arguments
    if not args:
        script = "hello.py"
    else:
        script = args[0]
        args = args[1:] # BUGFIX: This line was missing in the original

    # Set the path based on sys.path and the script directory
    path = sys.path[:]
    path[0] = os.path.dirname(script)
    path = addpath + path
    if debug > 1:
        print("path:")
        for item in path:
            print("   ", repr(item))

    # Create the module finder and turn its crank
    mf = ModuleFinderEx(path, debug, exclude)
    for arg in args[:]: # BUGFIX: the original used 'for arg in args[1:]'
        if arg == '-m':
            domods = 1
            continue
        if domods:
            if arg[-2:] == '.*':
                mf.import_hook(arg[:-2], None, ["*"])
            else:
                mf.import_hook(arg)
        else:
            mf.load_file(arg)
    mf.run_script(script)
    if doreport:
        mf.report()
    return mf  # for -i debugging


if __name__ == "__main__":
    mf = test()

# This support script is executed as the entry point for py2exe.

import sys
if 0:
    ################################################################
    # XXX Remove later!
    class LOGGER:
        def __init__(self):
            self.softspace = None
            self.ofi = open(r"c:\comerror.txt", "w")
        def write(self, text):
            self.ofi.write(text)
            self.ofi.flush()
    sys.stderr = sys.stdout = LOGGER()
    sys.stderr.write("PATH is %s\n" % sys.path)
################################################################
# tell the win32 COM registering/unregistering code that we're inside
# of an EXE/DLL
import pythoncom
if not hasattr(sys, "frozen"):
    # standard exes have none.
    sys.frozen = pythoncom.frozen = 1
else:
    # com DLLs already have sys.frozen set to 'dll'
    pythoncom.frozen = sys.frozen

# Help out the gencache (later we will fix this!)
import win32com, win32api, sys, os, new
win32com.__gen_path__ = os.path.join(
                        win32api.GetTempPath(), "gen_py",
                        "%d.%d" % (sys.version_info[0], sys.version_info[1]))
win32com.gen_py = new.module("win32com.gen_py")
win32com.gen_py.__path__ = [ win32com.__gen_path__ ]
sys.modules[win32com.gen_py.__name__]=win32com.gen_py

# Add some extra imports here, just to avoid putting them as "hidden imports"
# anywhere else - this script has the best idea about what it needs.
# (and hidden imports are currently disabled :)
import win32com.server.policy, win32com.server.util

# Patchup sys.argv for our DLL
if sys.frozen=="dll" and not hasattr(sys, "argv"):
    sys.argv = [win32api.GetModuleFileName(sys.frozendllhandle)]
# We assume that py2exe has magically set com_module_names
# to the module names that expose the COM objects we host.
# Note that here all the COM modules for the app are imported - hence any
# environment changes (such as sys.stderr redirection) will happen now.
com_modules = []
try:
    for name in com_module_names:
        __import__(name)
        com_modules.append(sys.modules[name])
except NameError:
    print "This script is designed to be run from inside py2exe"
    sys.exit(1)
del name

# Disable linecache.getline() which is called by
# traceback.extract_stack() when an exception occurs to try and read
# the filenames embedded in the packaged python code.  This is really
# annoying on windows when the d: or e: on our build box refers to
# someone elses removable or network drive so the getline() call
# causes it to ask them to insert a disk in that drive.
import linecache
def fake_getline(filename, lineno):
    return ''
linecache.orig_getline = linecache.getline
linecache.getline = fake_getline

def get_classes(module):
    return [ob
            for ob in module.__dict__.values()
            if hasattr(ob, "_reg_progid_")
            ]

def DllRegisterServer():
    # Enumerate each module implementing an object
    import win32com.server.register
    for mod in com_modules:
        # register each class
        win32com.server.register.RegisterClasses(*get_classes(mod))
        # see if the module has a custom registration function.
        extra_fun = getattr(mod, "DllRegisterServer", None)
        if extra_fun is not None:
            extra_fun()

def DllUnregisterServer():
    # Enumerate each module implementing an object
    import win32com.server.register
    for mod in com_modules:
        # see if the module has a custom unregister function.
        extra_fun = getattr(mod, "DllUnregisterServer", None)
        if extra_fun is not None:
            extra_fun()
        # and unregister each class
        win32com.server.register.UnregisterClasses(*get_classes(mod))

# Mainline code - executed always
# If we are running as a .EXE, check and process command-line args
if sys.frozen != "dll":
    import win32com.server.localserver
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i].lower()
        # support "exe /regserver"
        if arg.find("/reg") > -1 or arg.find("--reg") > -1 \
               or arg.find("-regserver") > -1:
            DllRegisterServer()
            break

        # support "exe /unreg...r"
        if arg.find("/unreg") > -1 or arg.find("--unreg") > -1 \
               or arg.find("-unregserver") > -1:
            DllUnregisterServer()
            break
        
        # MS seems to like /automate to run the class factories.
        if arg.find("/automate") > -1:
            clsids = []
            for m in com_modules:
                for k in get_classes(m):
                    clsids.append(k._reg_clsid_)
            # Fire up the class factories, and run the servers
            win32com.server.localserver.serve(clsids)
            # All servers dead - we are done!
            break
    else:
        # You could do something else useful here.
        import win32api
        win32api.MessageBox(0,
                            "This program hosts a COM Object and\r\nis started automatically",
                            "COM Object")

# This support script is executed as the entry point for py2exe.

import pythoncom
import sys

# tell the win32 COM registering/unregistering code that we're inside
# of an EXE/DLL
if not hasattr(sys, "frozen"):
    # standard exes have none.
    sys.frozen = pythoncom.frozen = 1
else:
    # com DLLs already have sys.frozen set to 'dll'
    pythoncom.frozen = sys.frozen

# We assume that py2exe has magically set com_module_names
# to the module names that expose the COM objects we host.
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
        # see if the module has a custom registration function.
        extra_fun = getattr(mod, "DllRegisterServer", None)
        if extra_fun is not None:
            extra_fun()
        # and register each class
        win32com.server.register.RegisterClasses(*get_classes(mod))

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
        if arg.find("/reg") > -1 or arg.find("--reg") > -1:
            DllRegisterServer()
            break

        # support "exe /unreg...r"
        if arg.find("/unreg") > -1 or arg.find("--unreg") > -1:
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
        win32api.MessageBox(0, "This program hosts a COM Object and\r\nis started automatically", "COM Object")

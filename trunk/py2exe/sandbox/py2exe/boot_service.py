# boot_service.py
import sys
# We assume that py2exe has magically set service_module_names
# to the module names that expose the services we host.
service_modules = []
try:
    for name in service_module_names:
        __import__(name)
        service_modules.append(sys.modules[name])
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

# nothing more to do!

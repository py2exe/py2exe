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

# nothing more to do!

# boot_service.py
import sys
import os
import servicemanager
import win32serviceutil
# We assume that py2exe has magically set service_module_names
# to the module names that expose the services we host.
service_klasses = []
try:
    for name in service_module_names:
        mod = __import__(name)
        for ob in mod.__dict__.values():
            if hasattr(ob, "_svc_name_"):
                service_klasses.append(ob)
except NameError:
    print "This script is designed to be run from inside py2exe"
    sys.exit(1)

if not service_klasses:
    raise RuntimeError, "No service classes found"

# Event source records come from servicemanager
evtsrc_dll = os.path.abspath(servicemanager.__file__)

# Tell the Python servicemanager what classes we host.
if len(service_klasses)==1:
    k = service_klasses[0]
    # One service - make the event name the same as the service.
    servicemanager.Initialize(k._svc_name_, evtsrc_dll)
    # And the class that hosts it.
    servicemanager.PrepareToHostSingle(k)
else:
    # Multiple services (NOTE - this hasn't been tested!)
    # Use the base name of the exe as the event source
    servicemanager.Initialize(os.path.basename(sys.executable), evtsrc_dll)
    for k in service_klasses:
        servicemanager.PrepareToHostMultiple(k._svc_name_, k)

# Simulate the old py2exe command line handling (to some extent)
# This could do with some re-thought, although it still isn't clear to
# MarkH that win32serviceutil command line options are appropriate here.
if len(sys.argv)>1 and sys.argv[1]=="-install":
    for k in service_klasses:
        svc_display_name = getattr(k, "_svc_display_name_", k._svc_name_)
        win32serviceutil.InstallService(None, k._svc_name_, svc_display_name,
                                        exeName = sys.executable)
elif len(sys.argv)>1 and sys.argv[1]=="-remove":
    for k in service_klasses:
        win32serviceutil.RemoveService(k._svc_name_)
else:
    print "Connecting to the Service Control Manager"
    servicemanager.StartServiceCtrlDispatcher()

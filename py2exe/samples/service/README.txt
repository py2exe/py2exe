Building a service with py2exe

Thomas Heller, 2002/01/29

This directory contains a sample windows NT service implemented in
Python, which can be 'frozen' into an exe-file by py2exe.


Prerequisites:

   Windows NT (NT, 2000, XP). Win98 or ME does *NOT* work. I've tested
   it with Win2000 SP1.

   Python (1.5.2, 2.0, 2.1, or 2.2).

   Mark Hammond's win32all extensions, I've tested it with the lastesd
   builds (143 and up). ActiveState Python should also work (and
   includes Mark's extensions).


Bugs:

   This is the first py2exe release supporting services, it is
   probably somewhat buggy. Error reporting could be improved, so be
   careful.


Step-by-step instructions

1. Make sure the service works if run by Python in the usual way:

   a. Register the python service manager (has only to be done once):
      'python\win32\PythonService.exe register'

   b. Install it with 'python MyService.py install'

   c. Start it with 'python MyService.py start' or 'net start MyService'.

   d. Stop it again with 'python MyService.py stop' or 'net stop MyService'.

   e. Open the Event Log Viewer (Control Panel->Administrative Tools->Event Viewer).

   f. Open the Application log, you should see two entries like
      "The MyService service has started/stopped"

   g. Deinstall the service again with 'python MyService.py remove'.

2. Build the exe-file with py2exe

   Note: py2exe doesn't create single file standalone exe-files, it
   creates a directory containing an exe-file together with some dlls
   still needed.

   a. Build it with 'python setup.py py2exe' in this very directory.
   Note: Normally you would have to supply the '--service MyService'
   command line option. In this case this is unneeded, because it is
   specified in the 'setup.cfg' file in this directory.

   b. You will see a lot of output, but finally a subdirectory
   dist\MyService should be created, containing MyService.exe,
   together with some .dll and .pyd files.

3. Run the build executable

   a. Change into this directory, and register the exe-file as service
   by running it with 'MyService.exe -install'. The service will be
   registered with default options (manual startup, log in as
   LocalSystem).   

   b. Start the service by 'net start MyService', it should print
        The My Service service is starting.
	The My Service service was started successfully.

   c. Stop the service again by 'net stop MyService', it should print
        The My Service service is stopping.
	The My Service service was stopped successfully.

   d. Look into the event log as described under 1.f

   e. You can tweak the service options (startup mode, log on as, ...)
   in the Control Panel Services applet.

   f. You can unregister the service again by running 'MyService.exe -remove'.

Building COM servers with py2exe:

This directory contains a setup script to build a COM server with
py2exe.  You need Mark Hammond's win32all extensions, build 154 for
Python 2.2 or build 155 for Python 2.3.

The COM server will be the 'Python Interpreter' COM server sample
included in the win32all extensions.

Run the supplied 'setup_interp.py' script with the --com-dll
command line option to build an inprocess server, or the --com-exe
command line option to build a localserver.

For the inprocserver you need Python 2.3, it will not work with an older
Python version.

The localserver must be registered by calling the interp.exe file with
'-regserver' or '/regserver' command line option, or '/unregserver' or
'-unregserver' to unregister it again.

The inproc server must be registered/unregistered by calling its
DllRegisterServer or DllUnregisterServer entry points of the created
interp.dll. There are several ways to do this, if you don't know how
to do it, ask google ;-)

After the server is registered, you can try it with the supplied VB
script test_interp.vbs. One way to run this is by entering 'cscript
test_interp.vbs' on the command line.

Note that the inproc server does not work with Python clients using
the same version as the server itself, I hope to fix this in the
future.

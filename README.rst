py2exe for Python 3
===================

`py2exe` is a distutils extension which allows to build standalone
Windows executable programs (32-bit and 64-bit) from Python scripts;
Python 3.3 and later are supported.  It can build console executables,
windows (GUI) executables, windows services, and DLL/EXE COM servers.

py2exe for Python 2 is still available at
http://sourceforge.net/project/showfiles.php?group_id=15583.

.. contents::

Changes
-------

Version 0.9.2.2: Added support for six, cffi, pycparser, openssl.
Support cmdline_style ("py2exe", "pywin32", "custom") again for
windows services.
Several bugfixes, better error messages.


News
----

The C-runtime library for Python 3 does NOT need a windows manifest
any longer to load correctly (this is a feature of Python, not of
py2exe).

`py2exe` now contains a hooks module which contains information about
some standard packages.  The goal is to fine-tune the build process so
that no (at least less) warnings are emitted from modulefinder.

Thanks to a brand new modulefinder (based on Python's importlib)
py2exe can now find and extract modules even from packages you have
installed as zipped eggs.

py2exe now longer uses a `build` directory for temporary files.

It is planned to achive full compatibility with the setup-scripts for
Python 2; however this is probably not yet the case.


In addition to your beloved setup.py scripts :-), there is now also a
command-line utility which allows to build the exe without any effort.

Running

::

   py -3.4 -m py2exe.build_exe myscript.py

or (if you have the Python ``Scripts`` directory on your PATH):

::

   build_exe myscript.py


will create an executable `myscript.exe` in the `dist` subdirectory.

If you add the ``-W <setup-script.py>`` switch to the above command
line a *commented* ``setup.py`` script will be generated which can be
used to further customize the exe:

::

   py -3.4 -m py2exe myscript.py -W mysetup.py
   ... edit myssetup.py
   py -3.4 mysetup.py py2exe


Installation
------------

::

    py -3.4 -m pip install py2exe

or

::

    pip install py2exe


Using the builder
-----------------

Build runtime archive for a script:

::

        build_exe [-h] [-i modname] [-x modname] [-p package_name] [-O] [-s]
                  [-r] [-f modname] [-v] [-c] [-d DESTDIR] [-l LIBNAME]
                  [-b {0,1,2,3}] [-W setup_path]
		  [-svc service]
                  [script [script ...]]


positional arguments:
  script

optional arguments:
  -h, --help            show this help message and exit
  -i modname, --include modname
                        module to include
  -x modname, --exclude modname
                        module to exclude
  -p package_name, --package package_name
                        module to exclude
  -O, --optimize        use optimized bytecode
  -s, --summary         print a single line listing how many modules were
                        found and how many modules are missing
  -r, --report          print a detailed report listing all found modules, the
                        missing modules, and which module imported them.
  -f modname, --from modname
                        print where the module <modname> is imported.
  -v                    verbose output
  -c, --compress        create a compressed library
  -d DESTDIR, --dest DESTDIR
                        destination directory
  -l LIBNAME, --library LIBNAME
                        relative pathname of the python archive

  -b option, --bundle-files option
                       How to bundle the files:
                         3 - create script.exe, python.dll, extensions.pyd, others.dll.
                         2 - create script.exe, python.dll, others.dll.
                         1 - create script.exe, others.dll.
                         0 - create script.exe.

  -W setup_path, --write-setup-script setup_path
                        Do not build the executables; instead write a setup
                        script that allows further customizations of the build
                        process.

  -svc svnmodule, --service svcmodule
                        The name of a module that contains a service

Using a setup-script
--------------------

Creating an executable (or more than one at the same time) with a
setup-script works in the same way as for Python 2.  The command-line
switches are the same as before; but they are *NOT* compatible with
the command-line switches for the builder mentioned above.

Documentation about the setup-script and other usage tips are in the
wiki pages at http://www.py2exe.org.


The bundle-files option explained
---------------------------------

The applications that py2exe creates will always need the following
parts:

1. The exe-file(s) itself. py2exe can build several executables at the
   same time; this is especially useful if these are related to each
   other since some parts can be shared.
2. The python-dll.
3. The pure python modules needed to run the app.  The byte-code for these
   modules is always packed into a zip-archive.
4. Compiled python-extension modules.
5. Supporting dlls, if any.

The bundle-files option determines how these files are packed together
for your application.  This is explained with a script ``test_sqlite.py``
that simply contains this code:

::

    import sqlite3
    print(sqlite3)

The command to build the exe-file is:

::

    py2exe.build_exe test_sqlite.py -c --bundle-files <option>

The ``-c`` option specifies to create a compressed zip-archive.

``--bundle-files 3`` is the simplest way.  These files will be
created in a ``dist`` subdirectory, about 8 MB total size:

::

    test_sqlite.exe
    _bz2.pyd
    _ctypes.pyd
    _hashlib.pyd
    _lzma.pyd
    _socket.pyd
    _sqlite3.pyd
    _ssl.pyd
    _win32sysloader.pyd  
    pyexpat.pyd
    python34.dll
    pywintypes34.dll
    select.pyd
    sqlite3.dll
    unicodedata.pyd
    win32api.pyd
    win32evtlog.pyd

The zip-archive is appended to the test_sqlite.exe file itself, which
has a size of 1.5 MB in this case.

``--bundle-files 2`` will include all the Python extensions into the
appended zip-archive; they are loaded via special code at runtime
*without* being unpacked to the file-system.  The files in the
``dist`` directory now are these:

::

    test_sqlite.exe
    python34.dll
    sqlite3.dll

``--bundle-files 1`` will additionally pack the python-dll into the
zip-archive:

::

    test_sqlite.exe
    sqlite3.dll

``--bundle-files 0`` now finally creates a real single-file executable
of 6 MB:

::

    test_sqlite.exe

If you are building several related executables that you plan to
distribute together, it may make sense to specify a zip-archive shared
by all the exes with the ``--library libname`` option.  The
executables will then become quite small (about 25 kB), since nearly
all code will be in the separate shared archive.

*Note that not all applications will work with ``bundle-files`` set to
0 or 1*. Be sure to test them.



Bugs
----

Building isapi extensions is not supported: I don't use them so I will
not implement this.

The modulefinder does not yet support PEP420 implicit namespace packages.

py2exe for Python 3
===================

`py2exe` is a distutils extension which allows to build standalone
Windows executable programs from Python scripts; Python 3.3 and Python
3.4 are supported.

`py2exe` for ``Python 2`` is available at http://sourceforge.net/project/showfiles.php?group_id=15583

.. contents::


News
----

Create an exe-file with a simple command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to you beloved setup.py scripts, there is now a
command-line utility which allows to build the exe without any effort:

::

   py -3.3 -m py2exe.build_exe myscript.py

or (if you have the Python ``Scripts`` directory on your PATH):

::

   build_exe myscript.py


will create an executable `myscript.exe` in the `dist` subdirectory.

If you add the ``-W <setup-script.py>`` switch to the command line it
will write a *commented* ``setup.py`` script for you, which can be
customized further:

::

   py -3.3 -m py2exe myscript.py -W mysetup.py
   ... edit myssetup.py
   py -3.3 mysetup.py py2exe

Hooks
~~~~~

`py2exe` now contains a hooks module which allows to customize the
build-process.  The goal is to fine-tune the build process so that no
warnings are emitted from modulefinder.

The hooks module is the `py2exe\\hooks.py` file in your installation;
it currently contains hooks for quite some libraries.  Patches for
more libraries will gratefully be accepted.

Windows C-runtime library
~~~~~~~~~~~~~~~~~~~~~~~~~

The C-runtime library for Python 3 does NOT need a windows manifest
any longer, unless you have special requirements.

Compatibility with py2exe for Python 2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is planned to achive full compatibility with the setup-scripts for
Python 2; however this is probably not yet the case.

Installation
------------

::

    py -3.3 -m pip install py2exe

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
                        How to bundle the files. 3 - create an .exe, a zip-
                        archive, and .pyd files in the file system. 2 - create
                        .exe and a zip-archive that contains the pyd files.

  -W setup_path, --write-setup-script setup_path
                        Do not build the executables; instead write a setup
                        script that allows further customizations of the build
                        process.

  --service modname
                        The name of a module that contains a service


Using a setup-script
--------------------

Creating an executable (or more than one at the same time) with a
setup-script works in the same way as for Python 2.  The command-line
switches are the same as before; but they are *NOT* compatible with
the command-line switches for the builder mentioned above.

Bugs
----

Building isapi extensions is not supported: I don't use them so I will
not implement this.

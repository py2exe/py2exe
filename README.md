py2exe for Python 3
===================

`py2exe` is a distutils extension which allows to build standalone
Windows executable programs (32-bit and 64-bit) from Python scripts.
Python versions included in the  official development cycle are supported
(from 3.6 to 3.9 included). `py2exe` can build console executables
and windows (GUI) executables. Building windows services, and DLL/EXE
COM servers might work but it is not actively supported.

Development of `py2exe` is hosted here:
https://github.com/py2exe/py2exe.


Changes
----------------------------

Detailed changelog is published on [GitHub](https://github.com/py2exe/py2exe/releases/).

Version 0.11.0.0:
- New module finder `mf310` written as a wrapper around CPython `modulefinder.ModuleFinder`
- Add support for Python 3.10
- New hook for `scipy`
- `zipextimporter` can now be built as a standalone extension via its own setup script

Version 0.10.4.1:
- `ModuleFinder`: add support for the `pkg_resources.extern.VendorImporter` loader
- New hooks for `pkg_resources` and `infi`

Version 0.10.4.0:
- `zipextimporter` supports external modules that use multi-phase initialization (PEP 489)
- New hook for `selenium`
- `dllfinder` provides a new method to add data files in the zip archive

Version 0.10.3.1:
- New hook for `pycryptodomex`
- `ModuleFinder`: respect excludes list in `import_package`
- Updated hook for `matplotlib` >= 3.4.0

Version 0.10.3.0:
- New hook for supporting `matplotlib` 3.2 and higher.
- Fix for including implicit namespace packages as per PEP420.

Version 0.10.2.1:
- Patch `MyLoadLibrary` to support `ssl` with `bundle_files=0`.

Version 0.10.2.0:
- New module finder with support for implicit namespace packages (PEP 420).
- `DLLFinder` automatically excludes VC++ redist and Windows CRT DLLs from bundles.
- Several fixes for bundling software with `bundle_files<=2` (only the standard library
  is supported, other dependencies may or may not work).
- New hooks for `pycryptodome` and `shapely`.

Version 0.10.1.0:
- Add support for Python 3.9.
- Drop support for Python 3.5.
- New hooks for `urllib3` and `pandas`.

Version 0.10.0.2 (from versions 0.9.x):
- Introduce compatibility with Python 3.5, 3.6, 3.7, and 3.8.
- Drop compatibility with Python 3.4 and earlier.
- New or updated hooks for `certifi`, `numpy`, `tkinter`, `socket`,
`ssl`, and `six`.
- `build_exe`: the `zipfile=None` option has been removed.
- `runtime`: the Python interpreter DLL is no longer altered before
being inserted in the executable bundle.
- Several bugfixes, better error messages.


Installation
------------

```pip install py2exe```


Using a setup-script
--------------------

Documentation about the setup-script and other usage tips are in the
wiki pages at http://www.py2exe.org.


Using the builder
-----------------

The `build_exe` CLI is not actively supported at the moment. Users are
encouraged to create their own `setup.py` files. Documentation
on how to use the CLI can be found [here](https://github.com/py2exe/py2exe/blob/master/README_ORIGINAL.rst).


Known issues
------------

- Building isapi extensions is not supported.
- High-level methods or hooks to embed Qt plugins in the bundle (needed by
PySide2/PyQt5) are missing.


Credits
--------

Further informations about the original development of `py2exe` and other
usage guidelines can be found [in the original README](https://github.com/py2exe/py2exe/blob/master/README_ORIGINAL.rst).
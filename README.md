py2exe for Python 3
===================

`py2exe` is a software to build standalone Windows executable programs from Python
scripts. `py2exe` can build console executables and windows (GUI) executables.
`py2exe` supports the Python versions* included in the [official development cycle](https://devguide.python.org/#status-of-python-branches).

Development of `py2exe` is hosted here: https://github.com/py2exe/py2exe.


Changes
----------------------------

The detailed changelog is published on [GitHub](https://github.com/py2exe/py2exe/releases/).

Version 0.13.0.0:
- Add support for Python 3.11
- Drop support for Python 3.7
- Drop support for `win32` wheels
  - `win32` wheels are still built and shipped but are provided untested. Issues
    experienced when using these wheels will not be investigated.
    See https://github.com/py2exe/py2exe/discussions/157 for further information.
- Remove `build_exe` command line interface. Please use the `py2exe.freeze` API.

Version 0.12.0.2:
- Support `scipy` versions newer than 1.9.2.
- Fixed documentation for the `py2exe.freeze` API.

Version 0.12.0.1:
- Fixed an issue that prevented builds via the deprecated `setup.py` API.

Version 0.12.0.0:
- Introduce the new `py2exe.freeze` API. Documentation can be found [here](https://github.com/py2exe/py2exe/blob/master/docs/py2exe.freeze.md).
- Use of the `setup.py py2exe` command and of `distutils` is deprecated as per PEP 632. Both
  these interfaces will be removed in the next major release. See [here](https://github.com/py2exe/py2exe/blob/master/docs/migration.md)
  for a migration guide.
- Add two hooks to fix the bundling of `winrt` and `passlib`.

Version 0.11.1.1:
- The log file for windows apps is now stored in `%APPDATA%` by default
- `ModuleFinder` now raises an explicit error if a required module is in `excludes`
- Restore hook functionality for `pkg_resources`
- The `Stderr.write` method used for windows apps now returns the number of written bytes

Version 0.11.1.0:
- Drop support for Python 3.6
- Include package metadata in the bundle archive (to be used by e.g. `importlib.metadata`)
- Fixed a bug that prevented to use the `optimize` option when `six` was in the bundle
- Fixed a bug that ignored the `optimize` flag for some packages

Version 0.11.0.1:
- Show again relative paths in Tracebacks that happen from the frozen application
  (#12 and #114)

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

Usage
---------------
Use the `py2exe.freeze` function as documented [here](https://github.com/py2exe/py2exe/blob/master/docs/py2exe.freeze.md).


Using a `setup.py` script or the builder
-----------------

Using a `setup.py` script with `py2exe` is deprecated. Please adapt your
scripts to use the new `freeze` API. This interface will be removed in the
next major release.

The `build_exe` (or `-m py2exe`) CLI was removed in version 0.13.0.0.

Known issues and notes
------------

- High-level methods or hooks to embed Qt plugins in the bundle (needed by
PySide2/PyQt5) are missing.
- (*) `win32` wheels are provided without testing. Users are encouraged to
use the `win_amd64` wheels (see #157).

Credits
--------

Further informations about the original development of `py2exe` and other
usage guidelines can be found [in the original README](https://github.com/py2exe/py2exe/blob/master/README_ORIGINAL.rst).

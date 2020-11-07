py2exe for Python 3
===================

`py2exe` is a distutils extension which allows to build standalone
Windows executable programs (32-bit and 64-bit) from Python scripts.
Python versions included in the  official development cycle are supported
(from 3.6 to 3.9 included). `py2exe` can build console executables
and windows (GUI) executables. Building windows services, and DLL/EXE
COM servers might work but it is not actively supported.

Development of `py2exe`is hosted here:
https://github.com/py2exe/py2exe.


Changes
----------------------------

Detailed changelog is published on [GitHub](https://github.com/py2exe/py2exe/releases/).

Version 0.10.1.0:
- Add support for Python 3.9.
- Drop support for Python 3.5.
- New hooks for `urllib3` and `pandas`.

Version 0.10.0.2 (from versions 0.9.x):
- Introduce compatibility with Python 3.5, 3.6, 3.7, and 3.8.
- Drop compatibility with Python 3.4 and earlier.
- New or updated hooks for `certifi`, `numpy`, `tkinter`, `socket`,
`ssl`, and `six`.
- `build_exe`: the `zipfile` option has been removed.
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
on how to use the CLI it can be found [here](https://github.com/py2exe/py2exe/blob/master/README_ORIGINAL.rst).


Known issues
------------

- The modulefinder does not fully support PEP420 implicit namespace packages.
- Building isapi extensions is not supported.
- Unit tests rely on `importlib.find_loader(name, path)` which has been
deprecated since Python 3.4.
- High-level methods or hooks to embed Qt plugins in the bundle (needed by
PysSide2/PyQt5) are missing.


Credits
--------

Further informations about the original development of `py2exe` and other
usage guidelines can be found [in the original README](https://github.com/py2exe/py2exe/blob/master/README_ORIGINAL.rst).
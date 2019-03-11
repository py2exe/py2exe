py2exe for Python 3
===================

`py2exe` is a distutils extension which allows to build standalone
Windows executable programs (32-bit and 64-bit) from Python scripts.
It can build console executables, windows (GUI) executables, windows
services, and DLL/EXE COM servers.

This is an attempt to keep using py2exe with Python 3.5 and modern modules. Credits to [mitre/caldera-py2exe](https://github.com/mitre/caldera-py2exe).

For further information see [the original README](README_ORIGINAL.rst).

Version History
-------

Version 0.9.2.9:
- fix a bug experienced when embedding `six.moves.urllib`.
- introduce a `add_datafile` method in runtime for hooks.
- new hook for `certifi`.

Version 0.9.2.8: introduce compatibility with Python 3.5.

Version 0.9.2.7: last version from upstream.

How to build and install on Python 3.5:
-------

- Install VS2015 or [VC++ Build Tools](http://landinghub.visualstudio.com/visual-cpp-build-tools)
- Open the "VS2015 x64 Native Tools Command Prompt" 
- Navigate to the py2exe folder
- Execute `python setup.py bdist`
- Execute `python setup.py bdist_egg`
- Install with easy_install

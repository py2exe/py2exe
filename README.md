py2exe for Python 3
===================

`py2exe` is a distutils extension that allows to build standalone
Windows executable programs (32-bit and 64-bit) from Python scripts.
It can build console executables, windows (GUI) executables, windows
services, and DLL/EXE COM servers.

This is an attempt to support py2exe on Python 3.5-3.6-3.7 and with modern modules. Credits to [mitre/caldera-py2exe](https://github.com/mitre/caldera-py2exe) for the fixes for Python 3.5.

For further information see [the original README](README_ORIGINAL.rst).

Version History
-------
Version 0.9.3.1:
read the [changelog](https://github.com/albertosottile/py2exe/releases/tag/v0.9.3.1).

Version 0.9.3.0:
- introduce compatibility with Python 3.7.
- automatic wheels building for cp35-cp36-cp37 on win32 and win_amd64.
- restored automatic tests on AppVeyor for all the platforms.

Version 0.9.2.9 (not released):
- build wheels for Python 3.5 and Python 3.6.
- fix a bug experienced when embedding `six.moves.urllib`.
- introduce a `add_datafile` method in runtime for hooks.
- new hook for `certifi`.

Version 0.9.2.8 (not released): introduce compatibility with Python 3.5.

Version 0.9.2.7: last version from upstream.

How to manually build and install:
-------

- Install VS2015 or [VC++ Build Tools](http://landinghub.visualstudio.com/visual-cpp-build-tools)
- Open the "VS2015 x64 Native Tools Command Prompt" 
- Navigate to the py2exe folder
- Execute `python setup.py bdist_wheel`
- Install with `pip`

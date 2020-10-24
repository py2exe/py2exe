py2exe for Python 3
===================

`py2exe` is a distutils extension that allows to build standalone
Windows executable programs (32-bit and 64-bit) from Python scripts.
It can build console executables, windows (GUI) executables, windows
services, and DLL/EXE COM servers.

This repository extends the support of py2exe to Python 3.5--3.8.

For further information see [the original README](README_ORIGINAL.rst).

How to install:
-------
- Get the latest wheels for your Python version/architecture from [releases](https://github.com/albertosottile/py2exe/releases).
- Install the downloaded wheel using `pip install` followed by the wheel filename. 

Version History
-------
Version 0.10.0.2: 
read the [changelog](https://github.com/albertosottile/py2exe/releases/tag/v0.10.0.2)

Version 0.10.0.1 - removed

Version 0.10.0.0 - removed

Version 0.9.3.2:
read the [changelog](https://github.com/albertosottile/py2exe/releases/tag/v0.9.3.2).

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
- Install VS2015 or VC++ Build Tools (details available [here](https://wiki.python.org/moin/WindowsCompilers#Microsoft_Visual_C.2B-.2B-_14.2_standalone:_Build_Tools_for_Visual_Studio_2019_.28x86.2C_x64.2C_ARM.2C_ARM64.29))
- Open the "VS2015 x64 Native Tools Command Prompt" 
- Navigate to the py2exe folder
- Install the dependencies `pip install pefile cachetools wheel`
- Execute `python setup.py bdist_wheel`
- Install the built wheel with `pip`

Credits
--------
Credits to [mitre/caldera-py2exe](https://github.com/mitre/caldera-py2exe) for the 
original fixes for Python 3.5.

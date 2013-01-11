Start working on a rewrite of py2exe.

Codename (in the repo) is py3exe.  Not sure if this will also be the
official name.

Planned features:

- Compatible with Python 2.7, and Python 3.x with the same codebase.

- A single 32-bit installer for all Python versions, a single 64-bit
  installer for all Python versions.

- Should work with 32-bit and 64-bit builds.

- MemoryLoadLibrary will no longer be used.

- Implement a 'hint' mechanism to find hidden imports and imports done
  by extension modules, runtime __path__ additions, and more; somewhat
  similar to PyInstaller hooks.  What does cx_Freeze do?

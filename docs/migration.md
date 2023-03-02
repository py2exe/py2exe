Migrate from `distutils.setup` to `py2exe.freeze`
===================

`py2exe` v0.12.0.0 introduced a new `freeze` API for using the software and deprecated the former `distutils.setup` and `setup.py py2exe` interfaces. Both these interfaces will be removed in the next major release of `py2exe` (see [PEP 632](https://peps.python.org/pep-0632), [the setuptools documentation](https://setuptools.pypa.io/en/latest/userguide/extension.html#final-remarks) and issue #127 for further information about this decision).

This document includes suggestion on how to migrate your existing freezing code to the new `freeze` API. Documentation for `freeze` is available [here](https://github.com/py2exe/py2exe/blob/master/docs/py2exe.freeze.md).

## Migration table

| Feature                     | Old syntax                                         | New syntax                               |
|-----------------------------|----------------------------------------------------|------------------------------------------|
| Run a freeze script         | `python setup.py py2exe`                           | `python freeze.py`                       |
| Import statements           | `from distutils.core import setup`<br/>`import py2exe` | `from py2exe import freeze`          |
| Freeze function             | `setup(console=...)`                               | `freeze(console=...)`                    |
| Service                     | `setup(service=...)`                               | `freeze(console=[myservice])`            |
| Pass options                | `options = {"py2exe": {"packages": ...}}`          | `options = {"packages": ...}`            |
| Use `includes` and similar  | `"includes": "os, time, requests"`                 | `"includes": ["os", "time", "requests"]` |
| Pass version info           | N/A                                                | Use the `version_info` argument          |
| `distutils` parameters      | `setup(maintainer=..., classifiers=...)`           | Do not pass these arguments to `freeze`  |

## Freezing script

Up to now, `py2exe` re-used the project `setup.py` script. With the `freeze` API you are free to use any Python script code you prefer. In this documentation and in the functional tests of this repository, we use `freeze.py` for this purpose, but this is a mere suggestion.

## Import statement

The `freeze` API has to be imported directly as in `from py2exe import freeze`. No need to import `distutils` or `setuptools` as before.

## Migrate the function call

A few details on how to go from a `setup` call to `freeze`:

- The `console`, `windows`, `data_files`, and `zipfile` arguments can be used with `freeze` as in `setup`.
- The `service` option has been removed. Instead use `freeze(console=[myservice])` and in your Target use `Target(script="myservice.py")`
- The `option` dictionary can also be re-used as it is, but we encourage to drop the `py2exe` extra key as support for it will be removed in the future.
- The `includes`, `excludes`, `packages`, and `dll_excludes` options should now be lists instead of comma-separated strings. The current syntax is still supported, but will be removed in the future.
- The `version_info` dictionary supports writing some information in the Properties of the frozen executable. This feature, despite advertised, was not working with older versions of `py2exe`. If you intend to use this feature, please convert your freezing script to the new API.
- All the other `distutils`-specific arguments, including but not limited to `name`, `author`, `version`, `url`, etc., are not supported by `freeze` and will raise `TypeError` if passed. Please remove these extra arguments from a call to `freeze` as `py2exe` is not designed to use them.


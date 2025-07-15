#!/usr/bin/python3,3
# -*- coding: utf-8 -*-
"""py2exe package
"""
DEPRECATION_MESSAGE_WIN32 = """
py2exe `win32` wheels are provided without support. Issues experienced when
using these wheels will not be investigated. Please upgrade your Python
interpreter to `win_amd64` whenever possible.

See https://github.com/py2exe/py2exe/discussions/157 for further
information.
"""

import logging
import sys

from argparse import Namespace

from . import runtime
from .version import __version__

from .patch_distutils import patch_distutils

is_64bits = sys.maxsize > 2**32
if not is_64bits:
    import warnings
    warnings.warn(DEPRECATION_MESSAGE_WIN32, DeprecationWarning, stacklevel=2)

patch_distutils()


def _fixup_version_info(version_info):
    if version_info:
        return Namespace(
                            version = version_info.get("version", ""),
                            file_description = version_info.get("description", None),
                            comments = version_info.get("comments", None),
                            company_name = version_info.get("company_name", None),
                            legal_copyright = version_info.get("copyright", None),
                            legal_trademarks = version_info.get("trademarks", None),
                            product_name = version_info.get("product_name", None),
                            product_version = version_info.get("product_version", version_info.get("version", "")),
                            internal_name = version_info.get("internal_name", None),
                            private_build = version_info.get("private_build", None),
                            special_build = version_info.get("special_build", None),
                        )
    return None


def freeze(console=[], windows=[], data_files=None, zipfile="library.zip", options={}, version_info={}):
    """Create a frozen executable from the passed Python script(s).

    Arguments:
        console (list of dict): paths of the Python files that will be frozen
            as console (CLI) executables. See below for the target dict syntax.
        windows (list of dict): paths of the Python files that will be frozen
            as windows (GUI) executables. See below for the target dict syntax.
        data_files (list): non-Python files that have to be added in the frozen
            bundle. Each element of the list is a tuple containing the destination
            path in the bundle and the source path of the data files.
        zipfile (str): target path of the archive that will contain all the Python
            packages and modules required by the frozen bundle.
            If this parameter is set to `None`, the archive will be attached
            to the target executable file.
        options (dict): options used to configure and customize the bundle.
            Supported values are listed below.
        version_info (dict): version strings and other information can be attached
            to the Windows executable file by configuring this dictionary.
            Supported values are listed below.

    Target dictionaries (to be used for `console` or `windows`):
        script (str): path of the Python module of the executable target.
        dest_base (str): optional, directory and basename of the executable.
            If a directory is contained, must be the same for all targets
        bitmap_resources (list): list of 2-tuples `(id, pathname)`.
            Bitmap files added in the bundle.
        icon_resources (list): list of 2-tuples `(id, pathname)`
            Icon used for the executable.
        other_resources (list): list of 3-tuples `(resource_type, id, datastring)`
            Other files added in the bundle.
        version_info (dict): optionally specifies version information for a given binary.
            Supported values are listed below.

    Options (`options`):
        includes (list): list of modules to include in the bundle.
        excludes (list): list of modules to exclude from the bundle.
        packages (list): list of packages to include in the bundle. Note: this option
            is NOT recursive. Only the modules in the first level of the package will
            be included.
        dll_excludes (list): list of DLLs to exclude from the bundle.
        dist_dir (str): target path of the bundle, default `dist`.
        compressed (int): if `1`, create a compressed destination library archive.
        unbuffered (int): if `1`, use unbuffered binary stdout and stderr.
        optimize (int): optimization level of the Python files embedded in the bundle
            default: `0`. Use `0` for `-O0`, `1` for `-O`, `2` for `-OO`.
        verbose (int): verbosity level of the freezing process, default `0`. Supported
            levels are `0--4`.
        bundle_files (int): select how to bundle the Python and extension DLL files,
            default `3` (all the files are copied alongside the frozen executable).
            See below for further information on this parameter.

    Bundle files levels (`bundle_files`): The py2exe runtime *can* use extension module
        by directly importing the from a zip-archive - without the need to unpack them
        to the file system. The bundle_files option specifies where the extension modules,
        the python DLL itself, and other needed DLLs are put.
        bundle_files == 3: Extension modules, the Python DLL and other needed DLLs are
            copied into the directory where the zipfile or the EXE/DLL files
            are created, and loaded in the normal way.

    **WARNING**: the following values are not supported in Python 3.12+! See
    https://github.com/py2exe/py2exe/issues/225 for further details.

        bundle_files == 2: Extension modules are put into the library ziparchive and loaded
            from it directly. The Python DLL and any other needed DLLs are copied into the
            directory where the zipfile or the EXE/DLL files are created, and loaded
            in the normal way.
        bundle_files == 1: Extension modules and the Python DLL are put into
            the zipfile or the EXE/DLL files, and everything is loaded without unpacking to
            the file system.  This does not work for some DLLs, so use with
            caution.
        bundle_files == 0: Extension modules, the Python DLL, and other needed DLLs are put
            into the zipfile or the EXE/DLL files, and everything is loaded
            without unpacking to the file system.  This does not work for
            some DLLs, so use with caution.

    Version information (`version_info`): Information passed in this dictionary are attached
        to all frozen executables and displayed in their Properties -> Details view.
        If you need to specify different version information for each of the frozen binaries
        you should add `version_info` dictionary to each of the `windows` and `console` targets.
        Supported keys:
        version (str): version number
        description (str): -
        comments (str): -
        company_name (str): -
        copyright (str): -
        trademarks (str): -
        product_name (str): -
        product_version (str): -
        internal_name (str): -
        private_build (str): -
        special_build (str): -

    Support limitations:
        `bundle_files <=2`: these settings do not work in Python 3.12+. See https://github.com/py2exe/py2exe/issues/225
            for further details. In general, these values are supported only for packages in the Python
            standard library. Issues occurring with external packages and lower values
            of `bundle_files` will not be investigated.
        `zipfile = None`: is not actively supported. Issues occurring when this
            option is used will not be investigated.
        Please use CPython from python.org: freezing from non-standard CPython installations,
            such as `conda` or Windows Store is not supported.
        `venv`: freezing from a virtual environment can cause unexpected errors for some
            scripts. We encourage the use of Docker Windows Containers for isolating
            the freezing environment.

    """
    console_targets = runtime.fixup_targets(console, "script")
    for target in console_targets:
        target.exe_type = "console_exe"
        target.version_info = _fixup_version_info(getattr(target, "version_info", None) or version_info)

    windows_targets = runtime.fixup_targets(windows, "script")
    for target in windows_targets:
        target.exe_type = "windows_exe"
        target.version_info = _fixup_version_info(getattr(target, "version_info", None) or version_info)

    # support the old dictionary structure with a global 'py2exe' key
    if 'py2exe' in options:
        options = options['py2exe']

    runtime_options = Namespace(
                        compress = options.get("compressed", 0),
                        unbuffered = options.get("unbuffered", 0),
                        optimize = options.get("optimize", 0),
                        includes = options.get("includes", []),
                        excludes = options.get("excludes", []),
                        packages = options.get("packages", []),
                        dll_excludes = options.get("dll_excludes", []),
                        bundle_files = options.get("bundle_files", 3),

                        script = console_targets + windows_targets,
                        service = [],
                        com_servers = [],

                        destdir = options.get("dist_dir", "dist"),
                        libname = zipfile,

                        verbose = options.get("verbose", 0),
                        report = False,
                        summary = False,

                        data_files = data_files,

                    )

    level = logging.INFO
    logging.basicConfig(level=level)

    builder = runtime.Runtime(runtime_options)
    builder.analyze()
    builder.build()

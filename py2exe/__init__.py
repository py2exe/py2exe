#!/usr/bin/python3,3
# -*- coding: utf-8 -*-
"""py2exe package
"""
import logging

from argparse import Namespace

from . import runtime
from .version import __version__

from .patch_distutils import patch_distutils

patch_distutils()

def fancy_split(str, sep=","):
    # a split which also strips whitespace from the items
    # passing a list or tuple will return it unchanged
    if str is None:
        return []
    if hasattr(str, "split"):
        return [item.strip() for item in str.split(sep)]
    return str

def freeze(console=[], windows=[], data_files=None, zipfile="library.zip", options={}):
    console_targets = runtime.fixup_targets(console, "script")
    for target in console_targets:
        target.exe_type = "console_exe"

    windows_targets = runtime.fixup_targets(windows, "script")
    for target in windows_targets:
        target.exe_type = "windows_exe"

    # support the old dictionary structure with a global 'py2exe' key
    if 'py2exe' in options:
        options = options['py2exe']

    runtime_options = Namespace(
                        compress = options.get("compressed", 0),
                        unbuffered = options.get("unbuffered", 0),
                        optimize = options.get("optimize", 0),
                        includes = fancy_split(options.get("includes", None)),
                        excludes = fancy_split(options.get("excludes", None)),
                        packages = fancy_split(options.get("packages", None)),
                        #dll_excludes = options.get("dll_excludes", None),
                        bundle_files = options.get("bundle_files", 3),

                        script = console_targets + windows_targets,
                        service = [],
                        com_servers = [],

                        destdir = options.get("dist_dir", "dist"),
                        libname = zipfile,

                        verbose = options.get("verbose", False),
                        report = False,
                        summary = False,

                        data_files = data_files,

                    )

    level = logging.INFO
    logging.basicConfig(level=level)

    builder = runtime.Runtime(runtime_options)
    builder.analyze()
    builder.build()

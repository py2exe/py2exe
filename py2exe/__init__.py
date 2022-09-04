#!/usr/bin/python3,3
# -*- coding: utf-8 -*-
"""py2exe package
"""

from argparse import Namespace

from . import runtime
from .version import __version__

from .patch_distutils import patch_distutils

patch_distutils()

def freeze(console=[], windows=[], data_files=None, zipfile="library.zip", options={}):
    console_targets = runtime.fixup_targets(console, "script")
    for target in console_targets:
        target.exe_type = "console_exe"

    windows_targets = runtime.fixup_targets(windows, "script")
    for target in windows_targets:
        target.exe_type = "windows_exe"

    runtime_options = Namespace(
                        compress = getattr(options, "compressed", 0),
                        unbuffered = getattr(options, "unbuffered", 0),
                        optimize = getattr(options, "optimize", 0),
                        includes = getattr(options, "includes", None),
                        excludes = getattr(options, "excludes", None),
                        packages = getattr(options, "packages", None),
                        dll_excludes = getattr(options, "dll_excludes", None),
                        bundle_files = getattr(options, "bundle_files", 3),

                        script = console_targets + windows_targets,
                        service = [],
                        com_servers = [],

                        destdir = getattr(options, "dist_dir", "dist"),
                        libname = zipfile,

                        verbose = getattr(options, "verbose", False),
                        report = False,
                        summary = False,

                        data_files = data_files,

                    )

    builder = runtime.Runtime(runtime_options)
    builder.analyze()
    builder.build()

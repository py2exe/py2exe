#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
import argparse
import logging
import os
import textwrap
from . import runtime

def main():
    parser = argparse.ArgumentParser(description="Build runtime archive for a script",
                                     formatter_class=argparse.RawTextHelpFormatter)

    # what to include, what to exclude...
    parser.add_argument("-i", "--include",
                        help="module to include",
                        dest="includes",
                        metavar="modname",
                        action="append"
                        )
    parser.add_argument("-x", "--exclude",
                        help="module to exclude",
                        dest="excludes",
                        metavar="modname",
                        action="append")
    parser.add_argument("-p", "--package",
                        help="module to exclude",
                        dest="packages",
                        metavar="package_name",
                        action="append")

    # how to compile the code...
    parser.add_argument("-O", "--optimize",
                        help="use optimized bytecode",
                        dest="optimize",
                        action="count")

    # reporting options...
    parser.add_argument("-s", "--summary",
                        help="""print a single line listing how many modules were
                        found and how many modules are missing""",
                        dest="summary",
                        action="store_true")
    parser.add_argument("-r", "--report",
                        help="""print a detailed report listing all found modules,
                        the missing modules, and which module imported them.""",
                        dest="report",
                        action="store_true")
    parser.add_argument("-f", "--from",
                        help="""print where the module <modname> is imported.""",
                        metavar="modname",
                        dest="show_from",
                        action="append")

    parser.add_argument("-v",
                        dest="verbose",
                        action="store_true")

    parser.add_argument("-c", "--compress",
                        dest="compress",
                        action="store_true")

    # what to build
    parser.add_argument("-d", "--dest",
##                        required=True,
                        default="dist",
                        help="""destination directory""",
                        dest="destdir")

    parser.add_argument("-b", "--bundle-files",
                        help=textwrap.dedent("""\
                        How to bundle the files:
                          3 - create script.exe, python.dll, extensions.pyd, others.dll.
                          2 - create script.exe, python.dll, others.dll.
                          1 - create script.exe, others.dll.
                          0 - create script.exe.
                          """),
                        choices=[0, 1, 2, 3],
                        type=int,
                        default=3)

    parser.add_argument("-W", "--write-setup-script",
                        help=textwrap.dedent("""\
                        Do not build the executables; instead write a setup script that allows
                        further customizations of the build process.
                        """),
                        metavar="setup_path",
                        dest="setup_path")

    # exe files to build...
    parser.add_argument("script",
                        metavar="script",
                        nargs="*",
                        )

    parser.add_argument("-svc", "--service",
                        help="""Build a service""",
                        metavar="service",
                        action="append",
                        )


    options = parser.parse_args()
    if not options.service and not options.script:
        parser.error("nothing to build")

    options.service = runtime.fixup_targets(options.service, "modules")
    for target in options.service:
        target.exe_type = "service"

    options.script = runtime.fixup_targets(options.script, "script")
    for target in options.script:
        if target.script.endswith(".pyw"):
            target.exe_type = "windows_exe"
        else:
            target.exe_type = "console_exe"
    
    if options.setup_path:
        if os.path.isfile(options.setup_path):
            message = "File %r already exists, are you sure you want to overwrite it? [yN]: "
            answer = input(message % options.setup_path)
            if answer not in "yY":
                print("Canceled.")
                return
        from .setup_template import write_setup
        write_setup(options)
        # no further action
        return

    options.data_files = None
    options.com_servers = []
    options.unbuffered = False

    level = logging.INFO if options.verbose else logging.WARNING
    logging.basicConfig(level=level)

    builder = runtime.Runtime(options)
    builder.analyze()
    builder.build()

if __name__ == "__main__":
    main()

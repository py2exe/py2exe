#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""setup script for py2exe.
"""

import os
import platform
import sys

from importlib import machinery

if platform.system() != 'Windows':
    raise RuntimeError("This package requires Windows")

if sys.version_info < (3, 7):
    raise RuntimeError("This package requires Python 3.7 or later")

############################################################################

from setuptools import setup

from py2exe_setuptools import Dist, Interpreter, BuildInterpreters

############################################################################

if 'MSC' in sys.version:
    python_dll_name = '\"python%d%d.dll\"' % sys.version_info[:2]
    python_dll_name_debug = '\"python%d%d_d.dll\"' % sys.version_info[:2]
else:
    python_dll_name = '\"libpython%d.%d.dll\"' % sys.version_info[:2]
    python_dll_name_debug = '\"libpython%d.%d_d.dll\"' % sys.version_info[:2]

def _is_debug_build():
    for ext in machinery.all_suffixes():
        if ext == "_d.pyd":
            return True
    return False

if _is_debug_build():
    macros = [("PYTHONDLL", python_dll_name_debug),
##              ("PYTHONCOM", '\\"pythoncom%d%d_d.dll\\"' % sys.version_info[:2]),
              ("_CRT_SECURE_NO_WARNINGS", '1')]
else:
    macros = [("PYTHONDLL", python_dll_name),
##              ("PYTHONCOM", '\\"pythoncom%d%d.dll\\"' % sys.version_info[:2]),
              ("_CRT_SECURE_NO_WARNINGS", '1'),]

macros.append(("Py_BUILD_CORE", '1'))
macros.append(("PYTHONHOME", ''))
macros.append(("PYTHONPATH", ''))

extra_compile_args = []
extra_link_args = []
subsys_console = []
subsys_windows = []
unicode_flags = []
dll_flags = []

if 'MSC' in sys.version:
    dll_flags = ["/DLL"]
    extra_compile_args.append("-IC:\\Program Files\\Microsoft SDKs\\Windows\\v7.0\\Include")
    extra_compile_args.append("-IC:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\include")
    extra_compile_args.append("-IC:\\Program Files (x86)\\Windows Kits\\10\\Include\\10.0.10586.0\\ucrt")
else:
    subsys_console = ["-mconsole"]
    subsys_windows = ["-mwindows"]
    unicode_flags = ["-municode"]
    if '64 bit' in sys.version:
        extra_link_args.append("-m64")
    else:
        extra_link_args.append("-m32")

if 0:
    # enable this to debug a release build
    extra_compile_args.append("/Od")
    extra_compile_args.append("/Z7")
    extra_link_args.append("/DEBUG")
    macros.append(("VERBOSE", "1"))

run_ctypes_dll = Interpreter("py2exe.run_ctypes_dll",
                             ["source/run_ctypes_dll.c",
                              "source/start.c",
                              "source/icon.rc",

                              "source/MemoryModule.c",
                              "source/MyLoadLibrary.c",
                              "source/_memimporter.c",
                              "source/actctx.c",

                              "source/python-dynload.c",
                              ],
                             libraries=["user32", "shell32"],
                             export_symbols=["DllCanUnloadNow,PRIVATE",
                                             "DllGetClassObject,PRIVATE",
                                             "DllRegisterServer,PRIVATE",
                                             "DllUnregisterServer,PRIVATE",
                                             ],
                             target_desc = "shared_library",
                             define_macros=macros,
                             extra_compile_args=extra_compile_args,
                             extra_link_args=extra_link_args + dll_flags + subsys_windows,
                             )

run = Interpreter("py2exe.run",
                  ["source/run.c",
                   "source/start.c",
                   "source/icon.rc",

                   "source/MemoryModule.c",
                   "source/MyLoadLibrary.c",
                   "source/_memimporter.c",
                   "source/actctx.c",

                   "source/python-dynload.c",
                   ],
                  libraries=["user32", "shell32"],
                  define_macros=macros,
                  extra_compile_args=extra_compile_args,
                  extra_link_args=extra_link_args + subsys_console + unicode_flags,
                  )

run_w = Interpreter("py2exe.run_w",
                    ["source/run_w.c",
                     "source/start.c",
                     "source/icon.rc",

                     "source/MemoryModule.c",
                     "source/MyLoadLibrary.c",
                     "source/_memimporter.c",
                     "source/actctx.c",

                     "source/python-dynload.c",
                     ],
                    libraries=["user32", "shell32"],
                    define_macros=macros,
                    extra_compile_args=extra_compile_args,
                    extra_link_args=extra_link_args + subsys_windows,
                    )

# The py2exe.resources name is special handled in BuildInterpreters;
# it will not include the python version and platform name. The final
# name will be 'resources.dll'.
#
# This is a resource only dll, so it needs no entry point.
#
# It seems that on SOME systems resources cannot be added correctly to
# this DLL when there are no resources in the dll initially; so for
# simplicity add the py2exe-icon.
resource_dll = Interpreter("py2exe.resources",
                           ["source/dll.c",
                            "source/icon.rc"],
                           target_desc = "shared_library",
                           extra_link_args=dll_flags,
                           )

interpreters = [run, run_w, resource_dll,
                run_ctypes_dll]


if __name__ == "__main__":
    cmdclass = {'build_interpreters': BuildInterpreters}

    setup(name="py2exe",
          version=open("py2exe/version.py").read().split("'")[1],
          description="Build standalone executables for Windows",
          long_description=open("README.md").read(),
          long_description_content_type="text/markdown",
          author="Thomas Heller",
          author_email="theller@ctypes.org",
          maintainer="Alberto Sottile",
          maintainer_email="alby128@gmail.com",
          url="http://www.py2exe.org/",
          project_urls={
                'Source': 'https://github.com/py2exe/py2exe',
                'Tracker': 'https://github.com/py2exe/py2exe/issues',
                'Documentation': 'https://github.com/py2exe/py2exe/blob/master/docs/py2exe.freeze.md',
          },
          license="MIT/X11 OR (MPL 2.0)",
          license_files=[
              "LICENSE.txt",
              "MIT-License.txt",
              "MPL2-License.txt",
              ],
          setup_requires=["wheel", "cachetools", "pefile", "packaging"],
          install_requires=["cachetools", "pefile"],
          platforms="Windows",
          python_requires='>=3.8, <3.13',

          classifiers=[
              "Development Status :: 4 - Beta",
              "Environment :: Console",
              "License :: OSI Approved :: MIT License",
              "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
              "Operating System :: Microsoft :: Windows",
              "Programming Language :: C",
              "Programming Language :: Python :: 3",
              "Programming Language :: Python :: 3.8",
              "Programming Language :: Python :: 3.9",
              "Programming Language :: Python :: 3.10",
              "Programming Language :: Python :: 3.11",
              "Programming Language :: Python :: 3.12",
              "Programming Language :: Python :: Implementation :: CPython",
              "Topic :: Software Development",
              "Topic :: Software Development :: Libraries",
              "Topic :: Software Development :: Libraries :: Python Modules",
              "Topic :: System :: Software Distribution",
              "Topic :: Utilities",
              ],

          distclass = Dist,
          cmdclass = cmdclass,
          interpreters = interpreters,
          py_modules=['zipextimporter'],
          packages=['py2exe', 'py2exe.vendor'],
          )

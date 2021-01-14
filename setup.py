#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
"""setup script for py2exe.
"""

import os
import sys

if sys.version_info < (3, 6):
    raise RuntimeError("This package requires Python 3.6 or later")

############################################################################

from setuptools import setup

from py2exe.py2exe_distutils import Dist, Interpreter, BuildInterpreters

############################################################################

if sys.version_info < (3, 9):
    python_dll_name = '\\"python%d%d.dll\\"' % sys.version_info[:2]
    python_dll_name_debug = '\\"python%d%d_d.dll\\"' % sys.version_info[:2]
else:
    python_dll_name = '\"python%d%d.dll\"' % sys.version_info[:2]
    python_dll_name_debug = '\"python%d%d_d.dll\"' % sys.version_info[:2]

def _is_debug_build():
    import imp
    for ext, _, _ in imp.get_suffixes():
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

extra_compile_args = []
extra_link_args = []

extra_compile_args.append("-IC:\\Program Files\\Microsoft SDKs\\Windows\\v7.0\\Include")
extra_compile_args.append("-IC:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\include")
extra_compile_args.append("-IC:\\Program Files (x86)\\Windows Kits\\10\\Include\\10.0.10586.0\\ucrt")

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
                             extra_link_args=extra_link_args + ["/DLL"],
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
                  extra_link_args=extra_link_args,
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
                    extra_link_args=extra_link_args,
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
                           extra_link_args=["/DLL"],
                           )

interpreters = [run, run_w, resource_dll,
                run_ctypes_dll]


if __name__ == "__main__":
    import py2exe

    cmdclass = {'build_interpreters': BuildInterpreters}

    setup(name="py2exe",
          version=py2exe.__version__,
          description="Build standalone executables for Windows",
          long_description=open("README.md").read(),
          long_description_content_type="text/markdown",
          author="Thomas Heller",
          author_email="theller@ctypes.org",
          maintainer="Alberto Sottile",
          maintainer_email="alby128@gmail.com",
          url="http://www.py2exe.org/",
          license="MIT/X11",
          install_requires=["cachetools", "pefile"],
          platforms="Windows",
          python_requires='>=3.6, <3.10',

          classifiers=[
              "Development Status :: 4 - Beta",
              "Environment :: Console",
              "License :: OSI Approved :: MIT License",
              "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
              "Operating System :: Microsoft :: Windows",
              "Programming Language :: C",
              "Programming Language :: Python :: 3",
              "Programming Language :: Python :: 3.6",
              "Programming Language :: Python :: 3.7",
              "Programming Language :: Python :: 3.8",
              "Programming Language :: Python :: 3.9",
              "Programming Language :: Python :: Implementation :: CPython",
              "Topic :: Software Development",
              "Topic :: Software Development :: Libraries",
              "Topic :: Software Development :: Libraries :: Python Modules",
              "Topic :: System :: Software Distribution",
              "Topic :: Utilities",
              ],

          distclass = Dist,
          cmdclass = cmdclass,
##          scripts = ["build_exe.py"],
          entry_points = {
              'console_scripts': ['build_exe = py2exe.build_exe:main'],
              },
          interpreters = interpreters,
          py_modules=['zipextimporter'],
          packages=['py2exe'],
          package_data={'py2exe':['MIT-License.txt', 'MPL2-License.txt']},
          )

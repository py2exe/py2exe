#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""setup script for py2exe.
"""

import os
import sys

if sys.version_info < (3, 3):
    raise RuntimeError("This package requires Python 3.3 or later")

############################################################################

from setuptools import setup
##from distutils.core import setup

from py2exe.py2exe_distutils import Dist, Interpreter, BuildInterpreters

############################################################################

def _is_debug_build():
    import imp
    for ext, _, _ in imp.get_suffixes():
        if ext == "_d.pyd":
            return True
    return False

if _is_debug_build():
    macros = [("PYTHONDLL", '\\"python%d%d_d.dll\\"' % sys.version_info[:2]),
##              ("PYTHONCOM", '\\"pythoncom%d%d_d.dll\\"' % sys.version_info[:2]),
              ("_CRT_SECURE_NO_WARNINGS", '1')]
else:
    macros = [("PYTHONDLL", '\\"python%d%d.dll\\"' % sys.version_info[:2]),
##              ("PYTHONCOM", '\\"pythoncom%d%d.dll\\"' % sys.version_info[:2]),
              ("_CRT_SECURE_NO_WARNINGS", '1')]

macros.append(("Py_BUILD_CORE", '1'))

extra_compile_args = []
extra_link_args = []

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
                             extra_link_args=extra_link_args,
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
                           extra_link_args=["/NOENTRY"],
                           )

interpreters = [run, run_w, resource_dll,
                run_ctypes_dll]

try:
    from wheel import bdist_wheel
except ImportError:
    my_bdist_wheel = None
else:
    class my_bdist_wheel(bdist_wheel.bdist_wheel):
        """We change the bdist_wheel command so that it creates a
        wheel-file compatible with Python 3.3 and Python 3.4 only by
        setting the impl_tag to py33.py34.
        """
        def get_tag(self):
            impl_tag, abi_tag, plat_tag = super().get_tag()
            return "py33.py34", abi_tag, plat_tag


if __name__ == "__main__":
    import py2exe

    cmdclass = {'build_interpreters': BuildInterpreters}
    if my_bdist_wheel is not None:
        cmdclass['bdist_wheel'] = my_bdist_wheel
    

    setup(name="py2exe",
          version=py2exe.__version__,
          description="Build standalone executables for Windows (python 3 version)",
          long_description=open("README.rst").read(),
          author="Thomas Heller",
          author_email="theller@ctypes.org",
    ##      maintainer="Jimmy Retzlaff",
    ##      maintainer_email="jimmy@retzlaff.com",
          url="http://www.py2exe.org/",
          license="MIT/X11",
          platforms="Windows",
    ##      download_url="http://sourceforge.net/project/showfiles.php?group_id=15583",

          classifiers=[
              "Development Status :: 4 - Beta",
              "Environment :: Console",
              "License :: OSI Approved :: MIT License",
              "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
              "Operating System :: Microsoft :: Windows",
              "Programming Language :: C",
              "Programming Language :: Python :: 3",
              "Programming Language :: Python :: 3.3",
              "Programming Language :: Python :: 3.4",
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
          )

# Local Variables:
# compile-command: "py -3.3 setup.py bdist_egg"
# End:

# c:\python33-64\lib\site-packages
# c:\python33-64\scripts

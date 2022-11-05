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

from setuptools.extension import Extension

############################################################################

python_dll_name = '\"python%d%d.dll\"' % sys.version_info[:2]
python_dll_name_debug = '\"python%d%d_d.dll\"' % sys.version_info[:2]

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

#macros.append(("Py_BUILD_CORE", '1'))

extra_compile_args = []
extra_link_args = []

extra_compile_args.append("-IC:\\Program Files\\Microsoft SDKs\\Windows\\v7.0\\Include")
extra_compile_args.append("-IC:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\include")
extra_compile_args.append("-IC:\\Program Files (x86)\\Windows Kits\\10\\Include\\10.0.10586.0\\ucrt")
extra_compile_args.append("/DSTANDALONE")

if 0:
    # enable this to debug a release build
    extra_compile_args.append("/Od")
    extra_compile_args.append("/Z7")
    extra_link_args.append("/DEBUG")
    macros.append(("VERBOSE", "1"))

_memimporter = Extension("_memimporter",
                        ["source/_memimporter.c",
                        "source/MemoryModule.c",
                        "source/MyLoadLibrary.c",
                        "source/actctx.c",
                        ],
                         libraries=["user32", "shell32"],
                         define_macros=macros + [("STANDALONE", "1")],
                         extra_compile_args=extra_compile_args,
                         extra_link_args=extra_link_args,
                         )

if __name__ == "__main__":

    setup(name="zipextimporter",
          version=open("py2exe/version.py").read().split("'")[1],
          description="Import Python extensions from zip files",
          long_description=open("README.md").read(),
          long_description_content_type="text/markdown",
          author="Thomas Heller",
          author_email="theller@ctypes.org",
          maintainer="Alberto Sottile",
          maintainer_email="alby128@gmail.com",
          url="http://www.py2exe.org/",
          license="MIT/X11",
          setup_requires=["wheel", "cachetools", "pefile"],
          install_requires=["cachetools", "pefile"],
          platforms="Windows",
          python_requires='>=3.8, <3.12',

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
              "Programming Language :: Python :: Implementation :: CPython",
              "Topic :: Software Development",
              "Topic :: Software Development :: Libraries",
              "Topic :: Software Development :: Libraries :: Python Modules",
              "Topic :: System :: Software Distribution",
              "Topic :: Utilities",
              ],

          ext_modules = [_memimporter],
          py_modules=['zipextimporter'],
          )

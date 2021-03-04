import setuptools
import py2exe

setuptools.setup(console=[{ "script": "numpy_test.py"}],
                 options={"py2exe": {
                              "packages": ['numpy']}})
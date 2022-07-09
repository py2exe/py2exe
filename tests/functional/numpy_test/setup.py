from setuptools import setup
import py2exe

setup(console=[{ "script": "numpy_test.py"}],
                 options={"py2exe": {
                              "packages": ['numpy']}})
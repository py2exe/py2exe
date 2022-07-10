from setuptools import setup
import py2exe

setup(console=[{ "script": "bundlefiles0_test.py"}],
    options={"py2exe": {
        "bundle_files": 0,
        "excludes": "tkinter, _ssl",
        "verbose": 4}},
     zipfile=None)

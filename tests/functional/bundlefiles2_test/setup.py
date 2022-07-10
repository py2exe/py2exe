from setuptools import setup
import py2exe

setup(console=[{ "script": "bundlefiles2_test.py"}],
    options={"py2exe": {
        "bundle_files": 2,
        "verbose": 4}})

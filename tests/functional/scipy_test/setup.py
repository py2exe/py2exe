from setuptools import setup
import py2exe

setup(console=[{ "script": "scipy_test.py"}],
      options={"py2exe": {
            "packages": ['scipy']}})
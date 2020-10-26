from distutils.core import setup
import py2exe

setup(console=[{ "script": "requests_test.py"}],
      options={"py2exe": {
            "packages": ['requests']}})

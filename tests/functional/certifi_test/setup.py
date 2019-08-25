from distutils.core import setup
import py2exe

setup(console=[{ "script": "certifi_test.py"}],
      options={"py2exe": {
            "packages": ['certifi']}})
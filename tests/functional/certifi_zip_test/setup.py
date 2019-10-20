from distutils.core import setup
import py2exe

setup(console=[{ "script": "certifi_zip_test.py"}],
      options={"py2exe": {
            "packages": ['certifi']}},
      zipfile="lib/libsync")
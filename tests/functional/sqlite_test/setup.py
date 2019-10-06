from distutils.core import setup
import py2exe

setup(console=[{ "script": "sqlite_test.py"}],
      options={"py2exe": {
            "includes": "sqlite3"}})
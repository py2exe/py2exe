from py2exe import setup

setup(console=[{ "script": "sqlite_test.py"}],
      options={"py2exe": {
            "includes": "sqlite3"}})
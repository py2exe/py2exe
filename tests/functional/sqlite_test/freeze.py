from py2exe import freeze

freeze(console=[{ "script": "sqlite_test.py"}],
      options={"py2exe": {
            "includes": "sqlite3"}})

from py2exe import freeze

freeze(console=[{ "script": "scipy_test.py"}],
      options={"py2exe": {
            "packages": ['scipy']}})
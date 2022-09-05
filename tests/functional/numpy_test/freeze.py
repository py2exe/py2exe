from py2exe import freeze

freeze(console=[{ "script": "numpy_test.py"}],
      options={"py2exe": {
            "packages": ['numpy']}})
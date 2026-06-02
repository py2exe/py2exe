from py2exe import freeze

freeze(console=[{"script": "pyphen_test.py"}],
      options={"py2exe": {
            "packages": ["pyphen"]}})

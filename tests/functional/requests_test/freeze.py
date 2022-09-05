from py2exe import freeze

freeze(console=[{ "script": "requests_test.py"}],
      options={"py2exe": {
            "packages": ['requests']}})

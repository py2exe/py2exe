from py2exe import freeze

freeze(console=[{ "script": "certifi_test.py"}],
      options={"py2exe": {
            "packages": ['certifi']}})
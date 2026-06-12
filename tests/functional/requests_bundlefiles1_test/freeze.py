from py2exe import freeze

freeze(console=[{ "script": "requests_bundlefiles1_test.py"}],
      options={"py2exe": {
            "bundle_files": 1,
            "packages": ['requests']}})

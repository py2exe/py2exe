from py2exe import freeze

freeze(console=[{ "script": "bundlefiles1_tk_test.py"}],
    options={"py2exe": {
        "bundle_files": 1,
        "verbose": 4}})

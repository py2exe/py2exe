from py2exe import freeze

freeze(console=[{ "script": "bundlefiles2_test.py"}],
    options={"py2exe": {
        "bundle_files": 2,
        "verbose": 4}})

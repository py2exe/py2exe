from py2exe import freeze

freeze(console=[{ "script": "bundlefiles0_test.py"}],
    options={"py2exe": {
        "bundle_files": 0,
        "excludes": "tkinter, _ssl",
        "verbose": 4}},
     zipfile=None)

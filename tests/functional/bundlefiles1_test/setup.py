from py2exe import setup

setup(console=[{ "script": "bundlefiles1_test.py"}],
    options={"py2exe": {
        "bundle_files": 1,
        "excludes": "tkinter",
        "verbose": 4}})

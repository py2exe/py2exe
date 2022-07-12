from py2exe import setup

setup(console=[{ "script": "bundlefiles0_ssl_test.py"}],
    options={"py2exe": {
        "bundle_files": 0,
        "excludes": "tkinter",
        "verbose": 4}},
     #zipfile=None
     )

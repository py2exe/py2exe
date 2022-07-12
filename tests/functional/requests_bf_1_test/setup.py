from py2exe import setup

setup(console=[{ "script": "requests_bf_1_test.py"}],
      options={"py2exe": {
            "bundle_files": 1,
            "packages": ['requests']}})

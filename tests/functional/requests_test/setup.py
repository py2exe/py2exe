from py2exe import setup

setup(console=[{ "script": "requests_test.py"}],
      options={"py2exe": {
            "packages": ['requests']}})

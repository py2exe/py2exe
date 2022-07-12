from py2exe import setup

setup(console=[{ "script": "scipy_test.py"}],
      options={"py2exe": {
            "packages": ['scipy']}})
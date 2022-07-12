from py2exe import setup

setup(console=[{ "script": "certifi_test.py"}],
      options={"py2exe": {
            "packages": ['certifi']}})
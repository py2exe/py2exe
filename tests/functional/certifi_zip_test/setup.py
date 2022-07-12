from py2exe import setup

setup(console=[{ "script": "certifi_zip_test.py"}],
      options={"py2exe": {
            "packages": ['certifi']}},
      zipfile="lib/libsync")
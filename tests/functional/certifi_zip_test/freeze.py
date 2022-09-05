from py2exe import freeze

freeze(console=[{ "script": "certifi_zip_test.py"}],
      options={"py2exe": {
            "packages": ['certifi']}},
      zipfile="lib/libsync")
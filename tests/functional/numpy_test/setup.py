from py2exe import setup

setup(console=[{ "script": "numpy_test.py"}],
      options={"py2exe": {"packages": ['numpy']}},
     )

from py2exe import setup

setup(
    console = [{"script": "wxPython_test.py"}],
    options={"py2exe": {"packages": ['wx']}},
    )

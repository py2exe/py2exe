from py2exe import freeze

freeze(
    console = [{"script": "wxPython_test.py"}],
    options={"py2exe": {"packages": ['wx']}},
    )

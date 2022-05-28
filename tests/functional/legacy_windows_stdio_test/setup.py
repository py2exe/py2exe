from distutils.core import setup
import py2exe

setup(
    console=[{"script": "legacy_windows_stdio_test.py"}],
    options={"py2exe": {"legacy_windows_stdio": True}},
)

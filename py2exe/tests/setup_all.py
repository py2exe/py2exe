from distutils.core import setup
import py2exe
import glob
import string, os

scripts = glob.glob("test*.py")

setup(name="test_py2exe",
      version="0.2.1",
      description="Testscripts for py2exe",
      author="Thomas Heller",
      author_email="theller@python.net",
      url="http://starship.python.net/crew/theller/py2exe/",

      scripts=scripts
      )

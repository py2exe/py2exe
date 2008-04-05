from distutils.core import setup
import py2exe

setup(
      script_args=['py2exe', '%s'],
      console=['%s'],
      zipfile=None,
     )

from distutils.core import setup
import py2exe

setup(name='MyService',
      description="A trivial windows NT service written in Python",
      version='0.3.0',
      scripts=['MyService.py'])

# setup_interp.py
# A distutils setup script for the "interp" sample.

from distutils.core import setup
import py2exe

setup(name="win32com 'interp' sample",
      scripts=["win32com.servers.interp"],
      output_base="interp" # Create 'interp.{exe/dll}
)

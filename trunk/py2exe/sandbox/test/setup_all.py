from distutils.core import setup
import py2exe

setup(#name="name",
      windows=["test_wx.py"],
##      service=["a.b.c.d"],
      com_server = ["win32com.servers.interp"],
      console=["hello.py"],
      zipfile="application",
      )

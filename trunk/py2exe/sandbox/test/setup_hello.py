from distutils.core import setup
import py2exe

setup(name="name",
##      com_dll=["win32com.servers.interp"],
##      com_exe=["win32com.servers.interp", "win32com.servers.dictionary"],
##      dll=["win32com.servers.interp"],
##      windows=["fpapp.fpanel"]
      console=["hello.py"]
      )

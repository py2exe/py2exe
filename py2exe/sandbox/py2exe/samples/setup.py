from distutils.core import setup
import py2exe

test_wmi = dict(
    script = "test_wmi.py",
    )

test_wx_console = dict(
    script = "test_wx.py",
    dest_base = "test_wx_console")

setup(
    options = {"py2exe": {"typelibs":
               [('{565783C6-CB41-11D1-8B02-00600806D9B6}', 0, 1, 2)]}},
    zipfile = "lib/shared.zip",
    service = ["MyService"],
    com_server = ["win32com.servers.interp"],
    console = ["hello.py", test_wx_console, test_wmi],
    windows = ["test_wx.py"],
    )

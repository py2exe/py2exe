from distutils.core import setup
import py2exe

test_wx_console = dict(
    script = "test_wx.py",
    dest_base = "test_wx_console")

setup(
    zipfile = "lib/shared.zip",
    service = ["MyService"],
    com_server = ["win32com.servers.interp"],
    console = ["hello.py", test_wx_console],
    windows = ["test_wx.py"]
    )

"""
C:\>\python22\lib\site-packages\win32com\client\makepy -i
Microsoft Excel 8.0 Object Library
 {00020813-0000-0000-C000-000000000046}, lcid=0, major=1, minor=2
 >>> # Use these commands in Python code to auto generate .py support
 >>> from win32com.client import gencache
 >>> gencache.EnsureModule('{00020813-0000-0000-C000-000000000046}', 0, 1, 2)

C:\>
"""
import win32com.client

# Excel 8.0 Type Library
win32com.client.gencache.EnsureModule('{00020813-0000-0000-C000-000000000046}', 0, 1, 2)

##import win32com.gen_py
##mod = __import__("win32com.gen_py.00020813-0000-0000-C000-000000000046x0x1x2")


d = win32com.client.Dispatch("Excel.Application")
print win32com.client.constants.xlAscending

##print dir(win32com.client.constants)

##import sys, pprint
##for name, mod in sys.modules.items():
##    if name.startswith("win32com.gen_py") and mod is not None:
##        print name

##print win32com.__path__

##import win32com.gen_py
##print win32com.gen_py.__path__

##mod = __import__("win32com.gen_py.00020813-0000-0000-C000-000000000046x0x1x2")

##print getattr(mod.gen_py, "00020813-0000-0000-C000-000000000046x0x1x2")
##print win32com.client.constants.xlDescending

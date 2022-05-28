import ctypes
import pprint
import sys

assert ctypes.c_int.in_dll(ctypes.pythonapi, "Py_LegacyWindowsStdioFlag").value == 1

if sys.version_info[:2] >= (3, 8):
    ctypes.pythonapi._Py_GetConfigsAsDict.restype = ctypes.py_object
    assert ctypes.pythonapi._Py_GetConfigsAsDict()["config"]["legacy_windows_stdio"] == 1

import sys
import win32process
from win32com.client import Dispatch

parser = Dispatch("Scripting.FileSystemObject")

pyVer = "{}{}".format(sys.version_info[0],sys.version_info[1])
pyLibName = "python{}.dll".format(pyVer)
print("Looking for the path of {}".format(pyLibName))

for process in win32process.EnumProcessModules(-1):
    name = win32process.GetModuleFileNameEx(-1, process)
    if pyLibName in name:
        print(name)
        pyLibPath = name

out = parser.GetFileVersion(pyLibPath)
print("pywin32 test output: {}".format(out))

out_list = out.split('.')
assert int(out_list[0]) == sys.version_info[0]
assert int(out_list[1]) == sys.version_info[1]
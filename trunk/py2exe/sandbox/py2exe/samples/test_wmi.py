import wmi # Tim Golden's wmi module.

# Workaround for a bug in win32all 161, see Mark Hammond's download page:
import win32com.client.util

computer = wmi.WMI()

for item in computer.Win32_Process()[:2]:
    print item

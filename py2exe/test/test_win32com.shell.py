from win32com.shell import shellcon, shell
print shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)

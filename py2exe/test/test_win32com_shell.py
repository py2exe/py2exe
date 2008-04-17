from win32com.shell import shellcon, shell

if __name__ == "__main__":
    print shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)

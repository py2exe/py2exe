# A setup script showing advanced features.
#
# Note that for the NT service to build correctly, you need at least
# win32all build 161, for the COM samples, you need build 163.

from distutils.core import setup
import py2exe
import sys

# If run without args, build executables, in quiet mode.
if len(sys.argv) == 1:
    sys.argv.append("py2exe")
    sys.argv.append("-q")

################################################################
# A program using early bound COM, needs the typelibs option below
test_wmi = dict(
    script = "test_wmi.py",
    )

################################################################
# A program using wxPython

# The manifest will be inserted as resource into test_wx.exe.  This
# gives the controls the Windows XP appearance (if run on XP ;-)
#
# Another option would be to store if in a file named
# test_wx.exe.manifest, and probably copy it with the data_files
# option.
#
manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32"
/>
<description>%(prog)s Program</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
'''

RT_MANIFEST = 24

test_wx = dict(
    script = "test_wx.py",
    other_resources = [(RT_MANIFEST, 1, manifest_template % dict(prog="test_wx"))],
    dest_base = "test_wx")

test_wx_console = dict(
    script = "test_wx.py",
    other_resources = [(RT_MANIFEST, 1, manifest_template % dict(prog="test_wx"))],
    dest_base = "test_wx_console")

################################################################
# a NT service, modules is required
myservice = dict(
    modules = ["MyService"]
    )

################################################################
# a COM server (exe and dll), modules is required
#
# If you only want a dll or an exe, comment out one of the create_xxx
# lines below.

interp = dict(
    modules = ["win32com.servers.interp"],
##    create_exe = False,
##    create_dll = False,
    )
################################################################
# COM pulls in a lot of stuff which we don't want or need.

excludes = ["pywin", "pywin.debugger", "pywin.debugger.dbgcon",
            "pywin.dialogs", "pywin.dialogs.list"]

setup(
    options = {"py2exe": {"typelibs":
                          [('{565783C6-CB41-11D1-8B02-00600806D9B6}', 0, 1, 2)],
                          # create a compressed zip archive
                          "compressed": 1,
                          "optimize": 2,
                          "excludes": excludes}},
    # The lib directory contains everything except the executables and the python dll.
    zipfile = "lib/shared.zip",
    service = [myservice],
    # a COM server, build as exe *and* dll
    com_server = ["win32com.servers.interp"],
    # other stuff
    console = [test_wx_console, test_wmi],
    windows = [test_wx],
    )

' A VBScript test harness for our test interpreter
' Running under cscript.exe is more useful than wscript.exe
' eg: cscript.exe test_interp.vbs

set interp = CreateObject("Python.Interpreter")
interp.Exec("import sys")
WScript.Echo "This Python object is being hosted in " & interp.Eval("sys.executable")
WScript.Echo "Path is " & interp.Eval("str(sys.path)")
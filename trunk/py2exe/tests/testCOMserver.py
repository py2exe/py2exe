import sys
import pythoncom

if hasattr(sys, 'importers'):
    pythoncom.frozen = 1
    
    
class HelloWorld:
    _reg_clsctx_ = pythoncom.CLSCTX_LOCAL_SERVER
    _reg_class_spec_ = "__main__.HelloWorld"
    _reg_clsid_ = "{B83DD222-7750-413D-A9AD-01B37021B24B}"
    _reg_desc_ = "Python Test COM Server"
    _reg_progid_ = "Python.TestServer"
    _public_methods_ = ['Hello']
    _public_attrs_ = ['softspace', 'noCalls']
    _readonly_attrs_ = ['noCalls']
    def __init__(self):
        self.softspace = 1
        self.noCalls = 0
    # __init__()
    
    def Hello(self, who):
        self.noCalls = self.noCalls + 1
        # insert "softspace" number of spaces
        return "Hello" + " " * self.softspace + str(who)

if __name__ == '__main__':
    print sys.argv
    if hasattr(sys, 'importers'):
        if '--register' in sys.argv[1:] \
           or '--unregister' in sys.argv[1:]:
            import win32com.server.register
            win32com.server.register.UseCommandLine(HelloWorld)
        else:
            from win32com.server import localserver
            localserver.main()
    else:
	import win32com.server.register
	win32com.server.register.UseCommandLine(HelloWorld)

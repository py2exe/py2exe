import sys
print "PATH", sys.path

from wxPython.wx import *

class MyApp(wxApp):
    def OnInit(self):
        frame = wxFrame(NULL, -1, "Hello from wxPython")
        frame.Show(true)
        self.SetTopWindow(frame)
        return true

app = MyApp(0)
app.MainLoop()

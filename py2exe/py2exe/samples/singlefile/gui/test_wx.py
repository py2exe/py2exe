from wxPython.wx import *

# By default the executables created by py2exe write output to stderr
# into a logfile and display a messagebox at program end when there
# has been any output.  This logger silently overrides the default
# behaviour by silently shallowing everything.

class logger:
    def write(self, text):
        pass # silently ignore everything

import sys
sys.stdout = sys.stderr = logger()

class MyFrame(wxFrame):
    def __init__(self, parent, ID, title, pos=wxDefaultPosition,
                 size=(200, 200), style=wxDEFAULT_FRAME_STYLE):
        wxFrame.__init__(self, parent, ID, title, pos, size, style)
        panel = wxPanel(self, -1)

        button = wxButton(panel, 1003, "Close Me")
        button.SetPosition(wxPoint(15, 15))
        EVT_BUTTON(self, 1003, self.OnCloseMe)
        EVT_CLOSE(self, self.OnCloseWindow)

        button = wxButton(panel, 1004, "Press Me")
        button.SetPosition(wxPoint(15, 45))
        EVT_BUTTON(self, 1004, self.OnPressMe)

    def OnCloseMe(self, event):
        self.Close(True)

    def OnPressMe(self, event):
        # This raises an exception
        x = 1 / 0

    def OnCloseWindow(self, event):
        self.Destroy()

class MyApp(wxApp):
    def OnInit(self):
        frame = MyFrame(NULL, -1, "Hello from wxPython")
        frame.Show(true)
        self.SetTopWindow(frame)
        return true

app = MyApp(0)
app.MainLoop()

import wx
app = wx.App()
frame = wx.Frame(None,title='hello')
title = frame.GetTitle()
print(title)
assert title == 'hello'

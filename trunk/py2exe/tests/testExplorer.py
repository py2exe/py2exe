#import copy_reg
#import types
#import string
#import cPickle

# testExplorer -

import string
import sys
import os
import win32com.client.dynamic
import win32api
import glob
import pythoncom

bVisibleEventFired = 0

class ExplorerEvents:
	def OnVisible(self, visible):
		global bVisibleEventFired
		bVisibleEventFired = 1
		print "Explorer is Visible", visible

def TestExplorerEvents():
	iexplore = win32com.client.DispatchWithEvents("InternetExplorer.Application", ExplorerEvents)
	iexplore.Visible = 1
	iexplore.Visible = 0
	iexplore.Visible = 1
	iexplore.Visible = 0
	iexplore.Visible = 1
	if not bVisibleEventFired:
		raise RuntimeError, "The IE event did not appear to fire!"
	iexplore.Quit()
	iexplore = None


def TestExplorer(iexplore):
	if not iexplore.Visible: iexplore.Visible = -1
	try:
##		iexplore.Navigate(r'c:\stat\index.html')
		iexplore.Navigate(r'http://starship.python.net/crew/theller/py2exe/')
	except pythoncom.com_error, details:
		print "Warning - could not got to py2exe homepage", details
#	for fname in glob.glob("..\\html\\*.html"):
#		print "Navigating to", fname
#		while iexplore.Busy:
#			win32api.Sleep(100)
#		iexplore.Navigate(win32api.GetFullPathName(fname))
	win32api.Sleep(4000)
	iexplore.Quit()

def TestAll():
	try:
		iexplore = win32com.client.dynamic.Dispatch("InternetExplorer.Application")
		TestExplorer(iexplore)

		win32api.Sleep(1000)
		iexplore = None

		# Test IE events.
		TestExplorerEvents()

		return

	finally:
		iexplore = None

if __name__=='__main__':
	TestAll()


from __future__ import division
# -*- coding: latin-1 -*-

import sys

for name in "argv path executable".split():
    print "sys.%s = " % name, getattr(sys, name)

##print "__file__", __file__
print "Hello, World"

import encodings
print "encodings.__file__", encodings.__file__

print u"Umlaute: �����ܵ"
print "1 / 2", 1/2
print 0x80000000

raw_input("Weiter?")

##from win32com.client.dynamic import Dispatch
##d = Dispatch("Word.Application")
##d.Visible = 1

##import time
##time.sleep(2)
##d.Quit()

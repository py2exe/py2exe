import pdb

import imputil
imputil._test_revamp()

pdb.set_trace()
import xml
print xml
del xml

import xml
print xml

print dir(xml)
for n in dir(xml):
  if n == '__builtins__':
    continue
  try:
    print n, getattr(xml, n)
  except:
    print "Exception on", n

import pprint, sys
pprint.pprint(sys.modules)

from xml.sax import saxexts
from xml.sax import saxlib
from xml.sax import saxutils
##import _xmlplus
parser = saxexts.make_parser("xml.sax.drivers.drv_pyexpat")
#import sys
#import pprint
#pprint.pprint(sys.modules)

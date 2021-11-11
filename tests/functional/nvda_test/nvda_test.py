import os
import sys
import globalVars
if hasattr(sys, "frozen"):
	globalVars.appPath = sys.prefix
else:
	globalVars.appPath = os.path.abspath(os.path.dirname(__file__))

import printData
printData.display()

import samplePKG
samplePKG.my_avesome_func('Import successful')

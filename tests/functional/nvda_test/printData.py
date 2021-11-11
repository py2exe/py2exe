import os
import globalVars
DATA_PATH = os.path.join(globalVars.appPath, globalVars.DATA_FILE_NAME)

def display():
	with open(DATA_PATH) as f:
		for line in f:
			print(line)

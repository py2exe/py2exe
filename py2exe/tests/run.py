import sys, os, string, glob

for script in glob.glob("test*.py"):
    name = os.path.splitext(script)[0]
    cmd = os.path.join("dist", name, name)
    raw_input ("RUN '%s'" % cmd)
    os.system(cmd)
    


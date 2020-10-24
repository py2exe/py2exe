import sys
import os

ins = 'Hello world'

f = open('mylog.log', 'w')
f.write(ins)
f.close()

with open('mylog.log') as f:
    out = f.readline().strip(r'\r\n')
    print(out)

assert ins == out

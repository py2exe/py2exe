import sys

try:
    __import__(sys.argv[1])
except Exception, details:
    print details
    sys.exit(1)
sys.exit(0)

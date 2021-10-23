import os.path
import sys

from glob import glob

folders = glob(f'{os.path.dirname(__file__)}/*/')
tests = list(map(os.path.normpath, folders))
tests = list(map(os.path.basename, tests))

if sys.version_info >= (3, 10):
    tests = [t for t in tests if t[0] != '_']

print(f'Enabled tests: {tests}')

with open('enabled_tests.txt', 'w') as f:
    for test in tests:
        f.write(f'{test}\n')

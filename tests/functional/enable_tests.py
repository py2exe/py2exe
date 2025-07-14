import os.path
import sys

from glob import glob

folders = glob(f'{os.path.dirname(__file__)}/*/')
tests = list(map(os.path.normpath, folders))
tests = list(map(os.path.basename, tests))

if sys.version_info >= (3, 10):
    tests = [t for t in tests if t[0] != '_']

if sys.version_info >= (3, 12):
    tests = [t for t in tests if 'bundlefiles' not in t]

# temporarily disable _wxPython test
# https://github.com/wxWidgets/Phoenix/issues/2246
try:
    tests.remove('_wxPython_test')
except ValueError:
    pass

# disable scipy tests on x86 (no wheels)
is_64bits = sys.maxsize > 2**32
if not is_64bits:
    try:
        tests.remove('scipy_test')
    except ValueError:
        pass

print(f'Enabled tests: {tests}')

with open('enabled_tests.txt', 'w') as f:
    for test in tests:
        f.write(f'{test}\n')

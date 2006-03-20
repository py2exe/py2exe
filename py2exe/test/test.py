"""
Run a series of test scripts before and after packaging with py2exe
and ensure that stdout/stderr and the return code are the same.
Several different modules are tested for compatibility purposes.

Running all tests requires the following packages:

ctypes
EasyDialogs for Windows
"""

import glob
import os
import shutil
import subprocess
import sys


# This is the default setup script. A custom script will be used for
# a test file called test_xyz.py if a corresponding setup_xyz.py is
# present.
py2exeTemplate = """
from distutils.core import setup
import py2exe
setup(script_args=['py2exe', '%s'], console = ['%s'])
"""

generatedSetup = 'generated_setup.py'


def clean():
    for path in ['build', 'dist']:
        if os.path.exists(path):
            shutil.rmtree(path)
    if os.path.exists(generatedSetup):
        os.remove(generatedSetup)


def run(*args):
    popen = subprocess.Popen(
                             args,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT
                            )
    output = popen.communicate()
    return popen.returncode, output


def main():
    for test in glob.glob('test_*.py'):
        print test

        # Execute script to get baseline
        baseline = run(sys.executable, test)
        exe = os.path.join('dist', os.path.splitext(test)[0] + '.exe')

        for option in ['--quiet', '--bundle=1', '--bundle=2', '--bundle=3', '--ascii', '--skip-archive']:
            # Build exe
            clean()
            print option
            if os.path.exists(test.replace('test_', 'setup_')):
                open(generatedSetup, 'wt').write(open(test.replace('test_', 'setup_'), 'rt').read() % (option, test))
            else:
                open(generatedSetup, 'wt').write(py2exeTemplate % (option, test))
            run(sys.executable, generatedSetup)

            # Run exe and test against baseline
            assert run(exe) == baseline

        print

    clean()


if __name__ == '__main__':
    main()

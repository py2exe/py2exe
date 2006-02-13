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


py2exeTemplate = "from distutils.core import setup; import py2exe; setup(script_args=['py2exe', '%s'], console = ['%s'])"


def clean():
    for path in ['build', 'dist']:
        if os.path.exists(path):
            shutil.rmtree(path)


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
            run(sys.executable, '-c', py2exeTemplate % (option, test))

            # Run exe and test against baseline
            assert run(exe) == baseline

        print

    clean()


if __name__ == '__main__':
    main()

"""
Run a series of test scripts before and after packaging with py2exe
and ensure that stdout/stderr and the return code are the same.
Several different modules are tested for compatibility purposes.

Running all tests requires the following packages:

ctypes
EasyDialogs for Windows
pywin32
subprocess
http://sourceforge.net/project/showfiles.php?group_id=6473
"""

import glob
import os
import shutil
import subprocess
import sys
import time


excludedTestFiles = dict(
    AMD64=['test_pysvn', 'test_win32com_shell.py'],
    Intel=[],
)

excludedTestOptions = dict(
    AMD64=['--bundle=1', '--bundle=2'],
    Intel=[],
)

options = {
    'test_noZipFile.py' : ['--quiet', '--compressed', '--bundle=1', '--bundle=2', '--bundle=3', '--ascii'],
}


# This is the default setup script. A custom script will be used for
# a test file called test_xyz.py if a corresponding setup_xyz.py is
# present.
py2exeTemplate = """
from distutils.core import setup
import py2exe
setup(console = ['%s'])
"""

generatedSetup = 'generated_setup.py'


def getPlatform(version):
    for platform in 'AMD64', 'Intel':
        if '(' + platform + ')' in version:
            return platform
    raise RuntimeError("Can't determine Intel vs. AMD64 from: " + version)


def PythonInterpreters(pattern):
    for folder in glob.glob(pattern):
        path = os.path.join(folder, 'python.exe')
        if os.path.exists(path):
            errorlevel, output = run(path, '-c', 'import sys; print sys.version')
            if errorlevel == 0:
                yield output.strip(), path


def shortVersion(version):
    return '%s-%s' % (version.split()[0], getPlatform(version))


def reasonForSkipping(interpreter, basename):
    errorlevel, output = run(interpreter, 'checkTestModule.py', basename)
    if errorlevel:
        return output.strip()
    else:
        return None


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
    return popen.returncode, output[0]


def main(interpreter_pattern=r'C:\Python*', test_pattern='test_*.py'):
    start = time.time()
    succeeded = {}
    skipped = {}
    failed = {}
    versions = []
    for version, interpreter in PythonInterpreters(interpreter_pattern):
        print 'Python', version
        versions.append(version)
        succeeded[version] = 0
        skipped[version] = 0
        failed[version] = 0
        for test in glob.glob(test_pattern):
            if test not in excludedTestFiles[getPlatform(version)]:
                print '   ', test
                basename = os.path.splitext(test)[0]
                reason = reasonForSkipping(interpreter, basename)
                if reason:
                    print '        SKIPPED: %s' % reason
                    skipped[version] += 1
                    continue

                # Execute script to get baseline
                baseline = run(interpreter, test)
                exe = os.path.join('dist', basename + '.exe')
                exe2 = os.path.join('dist', basename + '_2.exe')

                for option in options.get(test, ['--quiet', '--compressed', '--bundle=1', '--bundle=2', '--bundle=3', '--ascii', '--skip-archive']):
                    if option not in excludedTestOptions[getPlatform(version)]:
                        # Build exe
                        clean()
                        print '       ', option
                        if os.path.exists(test.replace('test_', 'setup_')):
                            open(generatedSetup, 'wt').write(open(test.replace('test_', 'setup_'), 'rt').read() % test)
                        else:
                            open(generatedSetup, 'wt').write(py2exeTemplate % test)
                        run(sys.executable, generatedSetup, 'py2exe', option)

                        # Run exe and test against baseline
                        os.rename(exe, exe2) # ensure that the exe works when renamed
                        out2 = run(exe2)
                        if out2 == baseline:
                            succeeded[version] += 1
                        else:
                            failed[version] += 1
                            print "FAILED."
                            print "\tExpected:", baseline
                            print "\t     Got:", out2
                            print

        clean()
        print

    columnWidth = max(map(len, map(shortVersion, versions)))
    format = '%' + str(columnWidth) + 's'
    format = ' '.join(4*[format])
    separator = ' '.join(4*[columnWidth*'-'])
    print round(time.time()-start, 1), 'seconds'
    print
    print format % ('', 'Succeeded', 'Skipped', 'Failed')
    print separator
    for version in versions:
        print format % (shortVersion(version), succeeded[version], skipped[version], failed[version])
    print separator
    print format % ('TOTAL', sum(succeeded.values()), sum(skipped.values()), sum(failed.values()))
    return sum(failed.values())


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))

setlocal
call vcvars32
rd /s/q build
call py20 setup.py build
REM call py20 setup.py build -g
call py20 setup.py bdist_wininst --dist-dir upload --target-version 2.0
del upload\py2exe*.zip
call py20 setup.py sdist -o
call py20 setup.py sdist -o
call py20 setup.py sdist --dist-dir upload
rd /s/q build
call py15 setup.py build
REM call py15 setup.py build -g
call py15 setup.py bdist_wininst --dist-dir upload --target-version 1.5
rd /s/q build
call py21 setup.py build
REM call py21 setup.py build -g
call py21 setup.py bdist_wininst --dist-dir upload --target-version 2.1
rd /s/q build
call py22 setup.py build
REM call py22 setup.py build -g
call py22 setup.py bdist_wininst --dist-dir upload --target-version 2.2

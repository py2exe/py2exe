rd /s/q build dist
call py20 setup.py build
call py20 setup.py build -g
call py20 setup.py bdist_wininst --dist-dir upload --target-version 2.0
call py20 setup.py sdist --dist-dir upload
rd /s/q build dist
call py15 setup.py build
call py15 setup.py build -g
call py15 setup.py bdist_wininst --dist-dir upload --target-version 1.5

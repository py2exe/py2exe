rmdir /s /q build
rmdir /s /q dist
C:\Python23\python.exe setup.py bdist_wininst
rmdir /s /q build
C:\Python24\python.exe setup.py bdist_wininst
rmdir /s /q build
del MANIFEST
C:\Python24\python.exe setup.py sdist -f

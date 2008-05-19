rm -rf dist
set DISTUTILS_USE_SDK=

rm -rf build
C:\Python23\python.exe setup.py bdist_wininst

rm -rf build
C:\Python24\python.exe setup.py bdist_wininst

rm -rf build
C:\Python25\python.exe setup.py bdist_wininst

set DISTUTILS_USE_SDK=1
call "C:\Program Files\Microsoft Platform SDK\setenv" /X64 /RETAIL
rm -rf build
C:\Python25amd64\python.exe setup.py bdist_msi
ren dist\py2exe-?.?.?.win32-py2.5.msi py2exe-?.?.?.win64-py2.5.amd64.msi

rm MANIFEST
C:\Python25\python.exe setup.py sdist -f

rm -rf build

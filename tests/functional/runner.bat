@echo off
set testname=%1
set TESTFAILED=0

cd %testname%
if exist .\requirements.txt pip install -r requirements.txt
python setup.py py2exe
if exist .\post_build.bat .\post_build.bat
cd dist
%testname%.exe || set TESTFAILED=1
goto :clean

:clean
cd ..
rmdir dist /s /q
if exist .\requirements.txt pip uninstall -r requirements.txt -y
cd ..
goto :exit

:exit
if %TESTFAILED% equ 1 (
    echo %testname% FAILED!!!
    exit /b -1
)


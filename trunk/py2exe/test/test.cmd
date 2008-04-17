@echo off

for /D %%f in (C:\Python??) do (
    "%%f\python.exe" test.py
    if errorlevel 1 goto fail
)
echo Success!!!

:fail

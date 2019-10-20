set testname=%1

cd %testname%
if exist .\requirements.txt pip install -r requirements.txt
python setup.py py2exe
cd dist
.\%testname%.exe
cd ..
rmdir dist /s /q
if exist .\requirements.txt pip uninstall -r requirements.txt -y
cd ..
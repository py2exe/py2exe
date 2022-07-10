from setuptools import setup
import py2exe
setup(
	console=[{"script": "nvda_test.py",},],
	data_files=[('.', ['data.txt'])],
    options={"py2exe": {
            "verbose": 4}}
)
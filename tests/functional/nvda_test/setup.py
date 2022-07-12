from py2exe import setup
setup(
	console=[{"script": "nvda_test.py",},],
	data_files=[('.', ['data.txt'])],
    options={"py2exe": {
            "verbose": 4}}
)
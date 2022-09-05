from py2exe import freeze

freeze(
	console=[{"script": "nvda_test.py",},],
	data_files=[('.', ['data.txt'])],
    options={"py2exe": {
            "verbose": 4}}
)
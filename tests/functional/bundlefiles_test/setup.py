from distutils.core import setup
import py2exe

mainfile ='bundlefiles_test.py'
exefile = 'bundlefiles_test'

setup(name="Main",
      version='0.0',
      description="Main script",
      scripts=[mainfile],
      windows=[{"script": mainfile,
                'company_name': "Company (c) 2019",
                'copyright': "Company (c) 2019",
                'dest_base': exefile}],
      data_files = [],
      options={"py2exe": {"unbuffered": True,
                          "optimize": 2,
                          "bundle_files": 0,
                          "compressed": False,
                          "includes": [],
                          "excludes" : [],
                          "packages": [],
                          "dll_excludes": []},},
      zipfile=None)

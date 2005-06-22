from distutils.core import setup, Extension

setup(name="memimporter",
      version="0.0.1",
      description="Import extension modules from zipfiles",
      long_description="Import extension modules from zipfiles",
      author="Thomas Heller",
      author_email="theller@python.net",
##      url="http://starship.python.net/crew/theller/py2exe/",
      license="MPL",
      platforms="Windows",
##      download_url="http://sourceforge.net/project/showfiles.php?group_id=15583",
      
      ext_modules = [Extension("_memimporter",
                               sources=["MemoryModule.c",
                                        "_memimporter.c"],
                               define_macros = [("DEBUG_OUTPUT", "1")],
                               # for ctypes <grin>
                               export_symbols=["MemoryLoadLibrary",
                                               "MemoryFreeLibrary",
                                               "MemoryGetProcAddress"],
                               libraries=["user32"])],
      py_modules = ["zipextimporter"],
      )

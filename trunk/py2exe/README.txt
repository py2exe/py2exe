Building py2exe from source
===========================

Unpack the zip-file, open a command prompt, and type

  python setup.py install

to build and install this version with release binaries.

If you also want to build the debugging binaries, use

  python setup.py build -g install

and you are done. You should have pythonxx_d.lib
available in the standard location before you try this.

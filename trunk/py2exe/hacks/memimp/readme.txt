Overview
========

zipextimporter.py contains an importer which allows to load Python
binary extension modules contained in a zip.archive, without unpacking
them to the file system.

Call the zipextimporter.install() function to install the import hook,
add a zip-file containing .pyd or .dll extension modules to sys.path,
and import them.

It uses the _memimporter extension which uses code from Joachim
Bauch's MemoryModule library.  This library emulates the win32 api
function LoadLibrary.

Sample usage
============

>>> import zipextimporter
>>> zipextimporter.install()
>>> import sys
>>> sys.path.append("lib.zip")
>>> import _socket
>>> _socket.__file__
'c:\\sf\\py2exe\\hacks\\memimp\\lib.zip\\_socket.pyd'
>>> _socket.__loader__
<ZipExtensionImporter at a74480>
>>>

Bugs
====

reload() on already imported extension modules does not work
correctly: It happily loads the extension a second time.

A new and improved py2exe for Python 2.3
========================================

Uses the zipimport mechanism, so it requires Python 2.3 or later.  The
zipimport mechanism is able to handle the early imports of the
warnings and also the encodings module which is done by Python.

Creates a single directory, which must be deployed completely.

(Most of this is based on ideas of Mark Hammond, he also implemented
most if the code:) Can create any number of console and gui
executables in this directory, plus optionally windows service exes,
plus optionally exe and dll com servers.  The com servers can expose
one or more com object classes.

All pure Python files are contained in a single zip archive, which is
shared by all the executables.  The zip archive may also be used by
programs embedding Python.  Since extension modules cannot be imported
from zipfiles, a simple pure Python loader is included in the zipfile
which loads the extension from the file system (without requiring that
the directory is in sys.path).

The executables run with only a single sys.path entry containing the
absolute filename of the zipfile archive. Absolute filenames are
constructed at runtime from the directory containing the executable,
and the zipfile name specified at build time.

The way has changed how build targets are specified in the setup
script. py2exe installs it own Distribution subclass, which enables
additional keyword arguments to the setup function:

console = [...] # list of scripts to convert into console executables
windows = [...] # list of scripts to convert into gui executables
com_servers = [...] # list of fully qualified class names to build into the exe com server
service = [...] # list of fully qualified class names to build into a service executable
isapi = [...], # list of script names to build into an ISAPI extension.
zipfile = "xxx.zip" # filename of the zipfile containing the pure Python modules

All of the above arguments are optional. The zipfile name defaults to
'library.zip'.

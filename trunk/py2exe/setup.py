##
##	   Copyright (c) 2000, 2001 Thomas Heller
##
## Permission is hereby granted, free of charge, to any person obtaining
## a copy of this software and associated documentation files (the
## "Software"), to deal in the Software without restriction, including
## without limitation the rights to use, copy, modify, merge, publish,
## distribute, sublicense, and/or sell copies of the Software, and to
## permit persons to whom the Software is furnished to do so, subject to
## the following conditions:
##
## The above copyright notice and this permission notice shall be
## included in all copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
## EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
## MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
## NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
## LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
## OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
## WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##

"""This package is a distutils extension to build
standalone windows executable programs from
python scripts.
"""

__version__ = "0.2.5"

# $Id$

import sys, os, string
from distutils.core import setup, Extension, Command
from distutils.dist import Distribution
from distutils.command import build_ext, build
from distutils.sysconfig import customize_compiler
from distutils.dep_util import newer_group
from distutils.errors import *

class Interpreter(Extension):
    pass


class Dist(Distribution):
    def __init__(self,attrs):
        self.interpreters = None
        Distribution.__init__(self,attrs)

    def has_interpreters(self):
        return self.interpreters and len(self.interpreters) > 0


class BuildInterpreters(build_ext.build_ext):
    description = "build special python interpreter stubs"

    def finalize_options(self):
        build_ext.build_ext.finalize_options(self)
        self.interpreters = self.distribution.interpreters

    def run (self):
        if not self.interpreters:
            return

        self.setup_compiler()

        # Now actually compile and link everything.
        for inter in self.interpreters:
            sources = inter.sources
            if sources is None or type(sources) not in (type([]), type(())):
                raise DistutilsSetupError, \
                      ("in 'interpreters' option ('%s'), " +
                       "'sources' must be present and must be " +
                       "a list of source filenames") % inter.name
            sources = list(sources)

            fullname = self.get_exe_fullname(inter.name)
            if self.inplace:
                # ignore build-lib -- put the compiled extension into
                # the source tree along with pure Python modules
                modpath = string.split(fullname, '.')
                package = string.join(modpath[0:-1], '.')
                base = modpath[-1]

                build_py = self.get_finalized_command('build_py')
                package_dir = build_py.get_package_dir(package)
                exe_filename = os.path.join(package_dir,
                                            self.get_exe_filename(base))
            else:
                exe_filename = os.path.join(self.build_lib,
                                            self.get_exe_filename(fullname))


            if not (self.force or \
                    newer_group(sources, exe_filename + '.exe', 'newer')):
                self.announce("skipping '%s' interpreter (up-to-date)" %
                              inter.name)
                continue # 'for' loop over all interpreters
            else:
                self.announce("building '%s' interpreter" % inter.name)

            sources = self.swig_sources(sources)

            extra_args = inter.extra_compile_args or []

            macros = inter.define_macros[:]
            for undef in inter.undef_macros:
                macros.append((undef,))

            objects = self.compiler.compile(sources,
                                            output_dir=self.build_temp,
                                            macros=macros,
                                            include_dirs=inter.include_dirs,
                                            debug=self.debug,
                                            extra_postargs=extra_args)

            if inter.extra_objects:
                objects.extend(inter.extra_objects)
            extra_args = inter.extra_link_args or []

            self.compiler.link_executable(
                objects, exe_filename, 
                libraries=self.get_libraries(inter),
                library_dirs=inter.library_dirs,
                runtime_library_dirs=inter.runtime_library_dirs,
                extra_postargs=extra_args,
                debug=self.debug)
            # cannot use upx any longer, since this collides with
            # the update resource code.

    # build_extensions ()

    def get_exe_fullname (self, inter_name):
        if self.package is None:
            return inter_name
        else:
            return self.package + '.' + inter_name

    def get_exe_filename (self, inter_name):
        ext_path = string.split(inter_name, '.')
        if self.debug:
            return apply(os.path.join, ext_path) + '_d'
        return apply(os.path.join, ext_path)

    def setup_compiler(self):
        # This method *should* be available separately in build_ext!
        from distutils.ccompiler import new_compiler

        # If we were asked to build any C/C++ libraries, make sure that the
        # directory where we put them is in the library search path for
        # linking interpreters.
        if self.distribution.has_c_libraries():
            build_clib = self.get_finalized_command('build_clib')
            self.libraries.extend(build_clib.get_library_names() or [])
            self.library_dirs.append(build_clib.build_clib)

        # Setup the CCompiler object that we'll use to do all the
        # compiling and linking
        self.compiler = new_compiler(compiler=self.compiler,
                                     verbose=self.verbose,
                                     dry_run=self.dry_run,
                                     force=self.force)
        customize_compiler(self.compiler)

        # And make sure that any compile/link-related options (which might
        # come from the command-line or from the setup script) are set in
        # that CCompiler object -- that way, they automatically apply to
        # all compiling and linking done here.
        if self.include_dirs is not None:
            self.compiler.set_include_dirs(self.include_dirs)
        if self.define is not None:
            # 'define' option is a list of (name,value) tuples
            for (name,value) in self.define:
                self.compiler.define_macro(name, value)
        if self.undef is not None:
            for macro in self.undef:
                self.compiler.undefine_macro(macro)
        if self.libraries is not None:
            self.compiler.set_libraries(self.libraries)
        if self.library_dirs is not None:
            self.compiler.set_library_dirs(self.library_dirs)
        if self.rpath is not None:
            self.compiler.set_runtime_library_dirs(self.rpath)
        if self.link_objects is not None:
            self.compiler.set_link_objects(self.link_objects)

    # setup_compiler()

# class BuildInterpreters

def InstallSubCommands():
    """Adds our own sub-commands to build and install"""
    has_interpreters = lambda self: self.distribution.has_interpreters()
    buildCmds = [('build_interpreters', has_interpreters)]
    build.build.sub_commands.extend(buildCmds)

InstallSubCommands()

############################################################################

class deinstall(Command):
    description = "Remove all installed files"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass
        
    def run(self):
        self.run_command('build')
        build = self.get_finalized_command('build')
        install = self.get_finalized_command('install')
        self.announce("removing files")
        for n in 'platlib', 'purelib', 'headers', 'scripts', 'data':
            dstdir = getattr(install, 'install_' + n)
            try:
                srcdir = getattr(build, 'build_' + n)
            except AttributeError:
                pass
            else:
                self._removefiles(dstdir, srcdir)

    def _removefiles(self, dstdir, srcdir):
        # Remove all files in dstdir which are present in srcdir
        assert dstdir != srcdir
        if not os.path.isdir(srcdir):
            return
        for n in os.listdir(srcdir):
            name = os.path.join(dstdir, n)
            if os.path.isfile(name):
                self.announce("removing '%s'" % name)
                if not self.dry_run:
                    try:
                        os.remove(name)
                    except OSError, details:
                        self.warn("Could not remove file: %s" % details)
                    if os.path.splitext(name)[1] == '.py':
                        # Try to remove .pyc and -pyo files also
                        try:
                            os.remove(name + 'c')
                        except OSError:
                            pass
                        try:
                            os.remove(name + 'o')
                        except OSError:
                            pass
            elif os.path.isdir(name):
                self._removefiles(name, os.path.join(srcdir, n))
                if not self.dry_run:
                    try:
                        os.rmdir(name)
                    except OSError, details:
                        self.warn("Are there additional user files?\n"\
                              "  Could not remove directory: %s" % details)
            else:
                self.announce("skipping removal of '%s' (does not exist)" %\
                              name)

############################################################################

run = Interpreter("py2exe.run",
                  ["source/run.c", "source/start.c", "source/icon.rc"],
                  include_dirs=["source/zlib"],
                  libraries=["zlibstat"],
                  library_dirs=["source/zlib/static32"],
                  extra_link_args=["/NOD:LIBC"],
                  define_macros=[("ZLIB_DLL", None), ("_WINDOWS", None)],
                  )

run_w = Interpreter("py2exe.run_w",
                    ["source/run_w.c", "source/start.c", "source/icon.rc"],
                    include_dirs=["source/zlib"],
                    libraries=["zlibstat", "user32"],
                    library_dirs=["source/zlib/static32"],
                    extra_link_args=["/NOD:LIBC"],
                    define_macros=[("ZLIB_DLL", None), ("_WINDOWS", None)],
                    )

from distutils import sysconfig
pythoninc = sysconfig.get_python_inc()

setup(name="py2exe",
      version=__version__,
      description="Build standalone executables for windows",
      long_description=__doc__,
      author="Thomas Heller",
      author_email="theller@python.net",
      url="http://starship.python.net/crew/theller/py2exe/",
      licence="MIT/X11",
##      platforms="Windows",
      
      distclass = Dist,
      cmdclass = {'build_interpreters': BuildInterpreters,
                  'deinstall': deinstall},

      ext_modules = [Extension("py2exe.py2exe_util",
                               sources=["source/py2exe_util.c"],
                               libraries=["imagehlp"]),
                    ],

## XXX clib has a bug: build_clib.get_source_files() method is missing!
##      libraries = [
##                   ("mylib",
##                    {"sources": ["source/start.c"],
##                     "include_dirs": [pythoninc, "source/zlib"],
##                     "macros": [("ZLIB_DLL", None), ("_WINDOWS", None)],
##                     },
##                   ),
##                   ],
      interpreters = [run, run_w],
      packages=['py2exe', 'py2exe.tools'],
      package_dir={'py2exe.tools': "tools" + sys.version[:3]},
      )

# Local Variables:
# compile-command: "py20 setup.py install"
# End:

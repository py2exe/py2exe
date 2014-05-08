# This file is only used when BUILDING py2exe.
import os, sys

from distutils.core import Extension
from distutils.dist import Distribution
from distutils.command import build_ext, build
from distutils.sysconfig import customize_compiler
from distutils.dep_util import newer_group
from distutils.errors import DistutilsError, DistutilsSetupError
from distutils.util import get_platform

# We don't need a manifest in the executable, so monkeypath the code away:
from distutils.msvc9compiler import MSVCCompiler
MSVCCompiler.manifest_setup_ldargs = lambda *args: None

class Interpreter(Extension):
    def __init__(self, *args, **kw):
        # Add a custom 'target_desc' option, which matches CCompiler
        # (is there a better way?
        if "target_desc" in kw:
            self.target_desc = kw['target_desc']
            del kw['target_desc']
        else:
            self.target_desc = "executable"
        Extension.__init__(self, *args, **kw)


class Dist(Distribution):
    def __init__(self,attrs):
        self.interpreters = None
        Distribution.__init__(self, attrs)

    def has_interpreters(self):
        return self.interpreters and len(self.interpreters) > 0

    def has_extensions(self):
        return False

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
                raise DistutilsSetupError(("in 'interpreters' option ('%s'), " +
                       "'sources' must be present and must be " +
                       "a list of source filenames") % inter.name)
            sources = list(sources)

            fullname = self.get_exe_fullname(inter.name)
            if self.inplace:
                # ignore build-lib -- put the compiled extension into
                # the source tree along with pure Python modules
                modpath = fullname.split('.')
                package = '.'.join(modpath[0:-1])
                base = modpath[-1]

                build_py = self.get_finalized_command('build_py')
                package_dir = build_py.get_package_dir(package)
                exe_filename = os.path.join(package_dir,
                                            self.get_exe_filename(base))
            else:
                exe_filename = os.path.join(self.build_lib,
                                            self.get_exe_filename(fullname))
            if inter.target_desc == "executable":
                exe_filename += ".exe"
            else:
                exe_filename += ".dll"

            if not (self.force or \
                    newer_group(sources + inter.depends, exe_filename, 'newer')):
                self.announce("skipping '%s' interpreter (up-to-date)" %
                              inter.name)
                continue # 'for' loop over all interpreters
            else:
                self.announce("building '%s' interpreter" % inter.name)

            extra_args = inter.extra_compile_args or []

            macros = inter.define_macros[:]
            for undef in inter.undef_macros:
                macros.append((undef,))

            objects = self.compiler.compile(sources,
                                            output_dir=self.build_temp,
                                            macros=macros,
                                            include_dirs=inter.include_dirs,
                                            debug=self.debug,
                                            extra_postargs=extra_args,
                                            depends=inter.depends)

            if inter.extra_objects:
                objects.extend(inter.extra_objects)
            extra_args = inter.extra_link_args or []

            if inter.export_symbols:
                # The mingw32 compiler writes a .def file containing
                # the export_symbols.  Since py2exe uses symbols in
                # the extended form 'DllCanUnloadNow,PRIVATE' (to
                # avoid MS linker warnings), we have to replace the
                # comma(s) with blanks, so that the .def file can be
                # properly parsed.
                # XXX MingW32CCompiler, or CygwinCCompiler ?
                from distutils.cygwinccompiler import Mingw32CCompiler
                if isinstance(self.compiler, Mingw32CCompiler):
                    inter.export_symbols = [s.replace(",", " ") for s in inter.export_symbols]
                    inter.export_symbols = [s.replace("=", "\t") for s in inter.export_symbols]

            # XXX - is msvccompiler.link broken?  From what I can see, the
            # following should work, instead of us checking the param:
            self.compiler.link(inter.target_desc,
                               objects, exe_filename,
                               libraries=self.get_libraries(inter),
                               library_dirs=inter.library_dirs,
                               runtime_library_dirs=inter.runtime_library_dirs,
                               export_symbols=inter.export_symbols,
                               extra_postargs=extra_args,
                               debug=self.debug)
    # build_extensions ()

    def get_exe_fullname (self, inter_name):
        if self.package is None:
            return inter_name
        else:
            return self.package + '.' + inter_name

    def get_exe_filename (self, inter_name):
        ext_path = inter_name.split('.')
        if self.debug:
            fnm = os.path.join(*ext_path) + '_d'
        else:
            fnm = os.path.join(*ext_path)
        if ext_path[-1] == "resources":
            return fnm
        return '%s-py%s.%s-%s' % (fnm, sys.version_info[0], sys.version_info[1], get_platform())

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
        try:
            self.compiler.initialize()
        except AttributeError:
            pass # initialize doesn't exist before 2.5
        customize_compiler(self.compiler)

        # And make sure that any compile/link-related options (which might
        # come from the command-line or from the setup script) are set in
        # that CCompiler object -- that way, they automatically apply to
        # all compiling and linking done here.
        if self.include_dirs is not None:
            self.compiler.set_include_dirs(self.include_dirs)
        if self.define is not None:
            # 'define' option is a list of (name, value) tuples
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

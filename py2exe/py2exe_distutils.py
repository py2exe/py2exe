# This file is only used when BUILDING py2exe.
import os, sys

from distutils.core import Extension
from distutils.dist import Distribution
from distutils.command import build_ext, build
from distutils.sysconfig import customize_compiler
from distutils.dep_util import newer_group
from distutils.errors import DistutilsError, DistutilsSetupError, DistutilsPlatformError
from distutils.errors import CCompilerError, CompileError
from distutils.util import get_platform
from distutils import log

# We don't need a manifest in the executable, so monkeypatch the code away:
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
        return self.has_interpreters()

    def has_ext_modules(self):
        return self.has_interpreters()


class BuildInterpreters(build_ext.build_ext):
    description = "build special python interpreter stubs"

    def finalize_options(self):
        super().finalize_options()
        self.interpreters = self.distribution.interpreters

    def run(self):
        # Copied from build_ext.run() except that we use
        # self.interpreters instead of self.extensions and
        # self.build_interpreters() instead of self.build_extensions()
        from distutils.ccompiler import new_compiler

        if not self.interpreters:
            return

        # Setup the CCompiler object that we'll use to do all the
        # compiling and linking
        self.compiler = new_compiler(compiler=self.compiler,
                                     verbose=self.verbose,
                                     dry_run=self.dry_run,
                                     force=self.force)
        customize_compiler(self.compiler)
        # If we are cross-compiling, init the compiler now (if we are not
        # cross-compiling, init would not hurt, but people may rely on
        # late initialization of compiler even if they shouldn't...)
        if os.name == 'nt' and self.plat_name != get_platform():
            self.compiler.initialize(self.plat_name)

        # And make sure that any compile/link-related options (which might
        # come from the command-line or from the setup script) are set in
        # that CCompiler object -- that way, they automatically apply to
        # all compiling and linking done here.
        if self.include_dirs is not None:
            self.compiler.set_include_dirs(self.include_dirs)
        if self.define is not None:
            # 'define' option is a list of (name,value) tuples
            for (name, value) in self.define:
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

        # Now actually compile and link everything.
        self.build_interpreters()

    def build_interpreters(self):

        for interp in self.interpreters:
            self.build_interp(interp)

    def build_interp(self, ext):
        sources = ext.sources
        if sources is None or not isinstance(sources, (list, tuple)):
            raise DistutilsSetupError(
                  "in 'interpreters' option (extension '%s'), "
                  "'sources' must be present and must be "
                  "a list of source filenames" % ext.name)
        sources = list(sources)

        ext_path = self.get_ext_fullpath(ext.name)

        if ext.target_desc == "executable":
            ext_path += ".exe"
        else:
            ext_path += ".dll"

        depends = sources + ext.depends
        if not (self.force or newer_group(depends, ext_path, 'newer')):
            log.debug("skipping '%s' extension (up-to-date)", ext.name)
            return
        else:
            log.info("building '%s' extension", ext.name)

        # First, compile the source code to object files.

        # XXX not honouring 'define_macros' or 'undef_macros' -- the
        # CCompiler API needs to change to accommodate this, and I
        # want to do one thing at a time!

        # Two possible sources for extra compiler arguments:
        #   - 'extra_compile_args' in Extension object
        #   - CFLAGS environment variable (not particularly
        #     elegant, but people seem to expect it and I
        #     guess it's useful)
        # The environment variable should take precedence, and
        # any sensible compiler will give precedence to later
        # command line args.  Hence we combine them in order:
        extra_args = ext.extra_compile_args or []

        macros = ext.define_macros[:]
        for undef in ext.undef_macros:
            macros.append((undef,))

        objects = self.compiler.compile(sources,
                                         output_dir=self.build_temp,
                                         macros=macros,
                                         include_dirs=ext.include_dirs,
                                         debug=self.debug,
                                         extra_postargs=extra_args,
                                         depends=ext.depends)

        # XXX -- this is a Vile HACK!
        #
        # The setup.py script for Python on Unix needs to be able to
        # get this list so it can perform all the clean up needed to
        # avoid keeping object files around when cleaning out a failed
        # build of an extension module.  Since Distutils does not
        # track dependencies, we have to get rid of intermediates to
        # ensure all the intermediates will be properly re-built.
        #
        self._built_objects = objects[:]

        # Now link the object files together into a "shared object" --
        # of course, first we have to figure out all the other things
        # that go into the mix.
        if ext.extra_objects:
            objects.extend(ext.extra_objects)
        extra_args = ext.extra_link_args or []

        # Detect target language, if not provided
##        language = ext.language or self.compiler.detect_language(sources)

        ## self.compiler.link_shared_object(
        ##     objects, ext_path,
        ##     libraries=self.get_libraries(ext),
        ##     library_dirs=ext.library_dirs,
        ##     runtime_library_dirs=ext.runtime_library_dirs,
        ##     extra_postargs=extra_args,
        ##     export_symbols=self.get_export_symbols(ext),
        ##     debug=self.debug,
        ##     build_temp=self.build_temp,
        ##     target_lang=language)

        # Hm, for Python 3.5 to link a shared library (instead of exe
        # or pyd) we need to add /DLL to the linker arguments.
        # Currently this is done in the setup script; should we do it
        # here?

        self.compiler.link(ext.target_desc,
                           objects, ext_path,
                           libraries=self.get_libraries(ext),
                           library_dirs=ext.library_dirs,
                           runtime_library_dirs=ext.runtime_library_dirs,
                           export_symbols=ext.export_symbols,
                           extra_postargs=extra_args,
                           debug=self.debug)


    # -- Name generators -----------------------------------------------

    def get_ext_filename (self, inter_name):
        ext_path = inter_name.split('.')
        if self.debug:
            fnm = os.path.join(*ext_path) + '_d'
        else:
            fnm = os.path.join(*ext_path)
        if ext_path[-1] == "resources":
            return fnm
        return '%s-py%s.%s-%s' % (fnm, sys.version_info[0], sys.version_info[1], get_platform())


def InstallSubCommands():
    """Adds our own sub-commands to build and install"""
    has_interpreters = lambda self: self.distribution.has_interpreters()
    buildCmds = [('build_interpreters', has_interpreters)]
    build.build.sub_commands.extend(buildCmds)

InstallSubCommands()

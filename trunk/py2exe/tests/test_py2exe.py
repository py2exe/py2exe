import string, sys, os

tests = []
TEST = tests.append
def skip_TEST(*args):
    pass

try:
    import pygame
except ImportError:
    print "pygame not tested"
else:
    TEST(r"""
>>> build('pygame-examples\liquid', """
"""data_files=[('data', ['pygame-examples\\data\\liquid.gif'])], """
"""args=['-e', 'win32api,zlib', """
"""'-i', 'pygame.version, pygame.base, pygame.rect, pygame.surflock, pygame.surface,pygame.cdrom,pygame.display,pygame.event,pygame.key,pygame.mouse,pygame.time,pygame.joystick,pygame.rwobject,pygame.image,pygame.mixer_music'])
Z Scripts.py2exe/
Z Scripts.py2exe/__main__.py
Z Scripts.py2exe/support.py
Z UserDict.pyc
Z copy.pyc
Z copy_reg.pyc
Z dospath.pyc
Z imputil.pyc
Z macpath.pyc
Z ntpath.pyc
Z os.pyc
Z popen2.pyc
Z posixpath.pyc
Z pre.pyc
Z pygame/
Z pygame/__init__.pyc
Z pygame/locals.pyc
Z pygame/version.pyc
Z re.pyc
Z repr.pyc
Z sre.pyc
Z sre_compile.pyc
Z sre_constants.pyc
Z sre_parse.pyc
Z stat.pyc
Z string.pyc
Z tempfile.pyc
Z types.pyc
------------------------------------------
F SDL.dll
F SDL_image.dll
F SDL_mixer.dll
F _sre.pyd
F base.pyd
F cdrom.pyd
F constants.pyd
F data
F display.pyd
F event.pyd
F image.pyd
F joystick.pyd
F key.pyd
F libpng1.dll
F liquid.exe
F mixer_music.pyd
F mouse.pyd
F python%(winver)s.dll
F rect.pyd
F rwobject.pyd
F smpeg.dll
F surface.pyd
F surflock.pyd
F time.pyd
F zlib.dll
++++++++++++++++++++++++++++++++++++++++++
""")


try:
    import _xmlplus
except:
    print "_xmlplus not tested"
else:
    TEST(r"""
>>> build('test_sax', args=['-p', '_xmlplus'])
warning: py2exe: *************************************************************************
warning: py2exe: * The following modules were not found:
warning: py2exe: *   xml_dc
warning: py2exe: *   xml.dom.SYNTAX_ERR
warning: py2exe: *   xml.dom.ext.reader.HtmlLib
warning: py2exe: *   xml.dom.DOMSTRING_SIZE_ERR
warning: py2exe: *   xml.dom.Node
warning: py2exe: *   os.path
warning: py2exe: *   xml.dom.XML_NAMESPACE
warning: py2exe: *   xml.parsers.sgmlop
warning: py2exe: *   xml.dom.Document
warning: py2exe: *   xml.dom.INVALID_MODIFICATION_ERR
warning: py2exe: *   xml.dom.INVALID_CHARACTER_ERR
warning: py2exe: *   xml.dom.DocumentType
warning: py2exe: *   xml.dom.INVALID_STATE_ERR
warning: py2exe: *   xml.dom.Attr
warning: py2exe: *   xml.dom.ext
warning: py2exe: *   xml.dom.html.HTMLCollection
warning: py2exe: *   xml.sax.SAXException
warning: py2exe: *   xml.dom.XMLNS_NAMESPACE
warning: py2exe: *   xml.dom.HierarchyRequestErr
warning: py2exe: *   xml.dom.WRONG_DOCUMENT_ERR
warning: py2exe: *   org.w3c.dom
warning: py2exe: *   pyversioncheck
warning: py2exe: *   XMLFactory
warning: py2exe: *   com.indelv.dom
warning: py2exe: *   xml.dom.NOT_FOUND_ERR
warning: py2exe: *   xml.dom.Entity
warning: py2exe: *   xml.sax.drivers.drv_xmlproc
warning: py2exe: *   xml.dom.NO_DATA_ALLOWED_ERR
warning: py2exe: *   fr.loria.xml
warning: py2exe: *   xml.dom.INDEX_SIZE_ERR
warning: py2exe: *   xml.dom.html.HTMLElement
warning: py2exe: *   ic
warning: py2exe: *   xml.dom.ext.Visitor
warning: py2exe: *   xml.sax.saxlib
warning: py2exe: *   xml.sax.drivers
warning: py2exe: *   org.apache.xerces.dom
warning: py2exe: *   xml.dom.NoModificationAllowedErr
warning: py2exe: *   java.io
warning: py2exe: *   SOCKS
warning: py2exe: *   xml.dom.html
warning: py2exe: *   xml.dom.INUSE_ATTRIBUTE_ERR
warning: py2exe: *   xml.dom.DOMImplementation
warning: py2exe: *   xml.sax.saxexts
warning: py2exe: *   xml.dom.implementation
warning: py2exe: *   xml.dom.ext.reader
warning: py2exe: *   org.brownell.xml
warning: py2exe: *   xml.dom.NAMESPACE_ERR
warning: py2exe: *   saxlib
warning: py2exe: *   org.brownell.xml.dom
warning: py2exe: *   java.net
warning: py2exe: *   com.sun.xml.tree
warning: py2exe: *   xml.dom.INVALID_ACCESS_ERR
warning: py2exe: *   org.openxml.parser
warning: py2exe: *   xml.dom.NodeIterator
warning: py2exe: *   XMLClient
warning: py2exe: *   xml.dom.NO_MODIFICATION_ALLOWED_ERR
warning: py2exe: *   xml.utils
warning: py2exe: *   xml.dom.NodeFilter
warning: py2exe: *   com.indelv.dom.util
warning: py2exe: *   xml.dom.NodeList
warning: py2exe: *   org.xml.sax
warning: py2exe: *   xml.dom.HIERARCHY_REQUEST_ERR
warning: py2exe: *   xml.parsers.xmlproc
warning: py2exe: *   xml.parsers.xmlproc.dtdparser
warning: py2exe: *   org.openxml.dom
warning: py2exe: *   xml.dom.InvalidAccessErr
warning: py2exe: *   org.apache.xerces.parsers
warning: py2exe: *   xml.dom.NamedNodeMap
warning: py2exe: *   xml.dom.NOT_SUPPORTED_ERR
warning: py2exe: *   xml.dom.IndexSizeErr
warning: py2exe: *   xml.unicode.iso8859
warning: py2exe: *   xml.parsers.pyexpat
warning: py2exe: *   xml.dom.Element
warning: py2exe: *   xml.parsers.xmlproc.xmlapp
warning: py2exe: *   XMLinter
warning: py2exe: *************************************************************************
Z Scripts.py2exe/
Z Scripts.py2exe/__main__.py
Z Scripts.py2exe/support.py
Z StringIO.pyc
Z UserDict.pyc
Z UserList.pyc
Z _xmlplus/
Z _xmlplus/__init__.pyc
Z _xmlplus/_checkversion.pyc
Z _xmlplus/dom/
Z _xmlplus/dom/Attr.pyc
Z _xmlplus/dom/CDATASection.pyc
Z _xmlplus/dom/CharacterData.pyc
Z _xmlplus/dom/Comment.pyc
Z _xmlplus/dom/DOMImplementation.pyc
Z _xmlplus/dom/Document.pyc
Z _xmlplus/dom/DocumentFragment.pyc
Z _xmlplus/dom/DocumentType.pyc
Z _xmlplus/dom/Element.pyc
Z _xmlplus/dom/Entity.pyc
Z _xmlplus/dom/EntityReference.pyc
Z _xmlplus/dom/Event.pyc
Z _xmlplus/dom/FtNode.pyc
Z _xmlplus/dom/NamedNodeMap.pyc
Z _xmlplus/dom/Node.pyc
Z _xmlplus/dom/NodeFilter.pyc
Z _xmlplus/dom/NodeIterator.pyc
Z _xmlplus/dom/NodeList.pyc
Z _xmlplus/dom/Notation.pyc
Z _xmlplus/dom/ProcessingInstruction.pyc
Z _xmlplus/dom/Text.pyc
Z _xmlplus/dom/TreeWalker.pyc
Z _xmlplus/dom/__init__.pyc
Z _xmlplus/dom/en_US.pyc
Z _xmlplus/dom/ext/
Z _xmlplus/dom/ext/Printer.pyc
Z _xmlplus/dom/ext/Visitor.pyc
Z _xmlplus/dom/ext/XHtmlPrinter.pyc
Z _xmlplus/dom/ext/__init__.pyc
Z _xmlplus/dom/ext/reader/
Z _xmlplus/dom/ext/reader/HtmlLib.pyc
Z _xmlplus/dom/ext/reader/HtmlSax.pyc
Z _xmlplus/dom/ext/reader/PyExpat.pyc
Z _xmlplus/dom/ext/reader/Sax.pyc
Z _xmlplus/dom/ext/reader/Sax2.pyc
Z _xmlplus/dom/ext/reader/Sax2Lib.pyc
Z _xmlplus/dom/ext/reader/__init__.pyc
Z _xmlplus/dom/html/
Z _xmlplus/dom/html/HTMLAnchorElement.pyc
Z _xmlplus/dom/html/HTMLAppletElement.pyc
Z _xmlplus/dom/html/HTMLAreaElement.pyc
Z _xmlplus/dom/html/HTMLBRElement.pycZ _xmlplus/dom/html/HTMLBaseElement.pyc
Z _xmlplus/dom/html/HTMLBaseFontElement.pyc
Z _xmlplus/dom/html/HTMLBodyElement.pyc
Z _xmlplus/dom/html/HTMLButtonElement.pyc
Z _xmlplus/dom/html/HTMLCollection.pyc
Z _xmlplus/dom/html/HTMLDListElement.pyc
Z _xmlplus/dom/html/HTMLDOMImplementation.pyc
Z _xmlplus/dom/html/HTMLDirectoryElement.pyc
Z _xmlplus/dom/html/HTMLDivElement.pyc
Z _xmlplus/dom/html/HTMLDocument.pyc
Z _xmlplus/dom/html/HTMLElement.pyc
Z _xmlplus/dom/html/HTMLFieldSetElement.pyc
Z _xmlplus/dom/html/HTMLFontElement.pyc
Z _xmlplus/dom/html/HTMLFormElement.pyc
Z _xmlplus/dom/html/HTMLFrameElement.pyc
Z _xmlplus/dom/html/HTMLFrameSetElement.pyc
Z _xmlplus/dom/html/HTMLHRElement.pyc
Z _xmlplus/dom/html/HTMLHeadElement.pyc
Z _xmlplus/dom/html/HTMLHeadingElement.pyc
Z _xmlplus/dom/html/HTMLHtmlElement.pyc
Z _xmlplus/dom/html/HTMLIFrameElement.pyc
Z _xmlplus/dom/html/HTMLImageElement.pyc
Z _xmlplus/dom/html/HTMLInputElement.pyc
Z _xmlplus/dom/html/HTMLIsIndexElement.pyc
Z _xmlplus/dom/html/HTMLLIElement.pyc
Z _xmlplus/dom/html/HTMLLabelElement.pyc
Z _xmlplus/dom/html/HTMLLegendElement.pyc
Z _xmlplus/dom/html/HTMLLinkElement.pyc
Z _xmlplus/dom/html/HTMLMapElement.pyc
Z _xmlplus/dom/html/HTMLMenuElement.pyc
Z _xmlplus/dom/html/HTMLMetaElement.pyc
Z _xmlplus/dom/html/HTMLModElement.pyc
Z _xmlplus/dom/html/HTMLOListElement.pyc
Z _xmlplus/dom/html/HTMLObjectElement.pyc
Z _xmlplus/dom/html/HTMLOptGroupElement.pyc
Z _xmlplus/dom/html/HTMLOptionElement.pyc
Z _xmlplus/dom/html/HTMLParagraphElement.pyc
Z _xmlplus/dom/html/HTMLParamElement.pyc
Z _xmlplus/dom/html/HTMLPreElement.pyc
Z _xmlplus/dom/html/HTMLQuoteElement.pyc
Z _xmlplus/dom/html/HTMLScriptElement.pyc
Z _xmlplus/dom/html/HTMLSelectElement.pyc
Z _xmlplus/dom/html/HTMLStyleElement.pyc
Z _xmlplus/dom/html/HTMLTableCaptionElement.pyc
Z _xmlplus/dom/html/HTMLTableCellElement.pyc
Z _xmlplus/dom/html/HTMLTableColElement.pyc
Z _xmlplus/dom/html/HTMLTableElement.pyc
Z _xmlplus/dom/html/HTMLTableRowElement.pyc
Z _xmlplus/dom/html/HTMLTableSectionElement.pyc
Z _xmlplus/dom/html/HTMLTextAreaElement.pyc
Z _xmlplus/dom/html/HTMLTitleElement.pyc
Z _xmlplus/dom/html/HTMLUListElement.pyc
Z _xmlplus/dom/html/__init__.pyc
Z _xmlplus/dom/html/generateHtml.pyc
Z _xmlplus/dom/javadom.pyc
Z _xmlplus/dom/minidom.pyc
Z _xmlplus/dom/pulldom.pyc
Z _xmlplus/marshal/
Z _xmlplus/marshal/__init__.pyc
Z _xmlplus/marshal/generic.pyc
Z _xmlplus/marshal/wddx.pyc
Z _xmlplus/marshal/xmlrpc.pyc
Z _xmlplus/parsers/
Z _xmlplus/parsers/__init__.pyc
Z _xmlplus/parsers/expat.pyc
Z _xmlplus/parsers/sgmllib.pyc
Z _xmlplus/parsers/xmlproc/
Z _xmlplus/parsers/xmlproc/__init__.pyc
Z _xmlplus/parsers/xmlproc/catalog.pyc
Z _xmlplus/parsers/xmlproc/charconv.pyc
Z _xmlplus/parsers/xmlproc/dtdparser.pyc
Z _xmlplus/parsers/xmlproc/errors.pyc
Z _xmlplus/parsers/xmlproc/namespace.pyc
Z _xmlplus/parsers/xmlproc/utils.pyc
Z _xmlplus/parsers/xmlproc/xcatalog.pyc
Z _xmlplus/parsers/xmlproc/xmlapp.pyc
Z _xmlplus/parsers/xmlproc/xmldtd.pyc
Z _xmlplus/parsers/xmlproc/xmlproc.pyc
Z _xmlplus/parsers/xmlproc/xmlutils.pyc
Z _xmlplus/parsers/xmlproc/xmlval.pyc
Z _xmlplus/sax/
Z _xmlplus/sax/__init__.pyc
Z _xmlplus/sax/_exceptions.pyc
Z _xmlplus/sax/drivers/
Z _xmlplus/sax/drivers/__init__.pyc
Z _xmlplus/sax/drivers/drv_htmllib.pyc
Z _xmlplus/sax/drivers/drv_ltdriver.pyc
Z _xmlplus/sax/drivers/drv_ltdriver_val.pyc
Z _xmlplus/sax/drivers/drv_pyexpat.pyc
Z _xmlplus/sax/drivers/drv_sgmllib.pyc
Z _xmlplus/sax/drivers/drv_sgmlop.pyc
Z _xmlplus/sax/drivers/drv_xmldc.pyc
Z _xmlplus/sax/drivers/drv_xmllib.pyc
Z _xmlplus/sax/drivers/drv_xmlproc.pyc
Z _xmlplus/sax/drivers/drv_xmlproc_val.pyc
Z _xmlplus/sax/drivers/drv_xmltoolkit.pyc
Z _xmlplus/sax/drivers/pylibs.pyc
Z _xmlplus/sax/drivers2/
Z _xmlplus/sax/drivers2/__init__.pyc
Z _xmlplus/sax/drivers2/drv_pyexpat.pyc
Z _xmlplus/sax/drivers2/drv_xmlproc.pyc
Z _xmlplus/sax/expatreader.pyc
Z _xmlplus/sax/handler.pyc
Z _xmlplus/sax/sax2exts.pyc
Z _xmlplus/sax/saxexts.pyc
Z _xmlplus/sax/saxlib.pyc
Z _xmlplus/sax/saxutils.pyc
Z _xmlplus/sax/writer.pyc
Z _xmlplus/sax/xmlreader.pyc
Z _xmlplus/unicode/
Z _xmlplus/unicode/__init__.pyc
Z _xmlplus/unicode/iso8859.pyc
Z _xmlplus/unicode/utf8_iso.pyc
Z _xmlplus/utils/
Z _xmlplus/utils/__init__.pyc
Z _xmlplus/utils/iso8601.pyc
Z _xmlplus/utils/qp_xml.pyc
Z anydbm.pyc
Z base64.pyc
Z codecs.pyc
Z copy.pyc
Z copy_reg.pyc
Z dospath.pyc
Z encodings/
Z encodings/__init__.pyc
Z encodings/aliases.pyc
Z formatter.pyc
Z ftplib.pyc
Z getopt.pyc
Z getpass.pyc
Z gopherlib.pyc
Z htmlentitydefs.pyc
Z htmllib.pyc
Z httplib.pyc
Z imputil.pyc
Z macpath.pyc
Z macurl2path.pyc
Z mimetools.pyc
Z mimetypes.pyc
Z ntpath.pyc
Z nturl2path.pyc
Z os.pyc
Z popen2.pyc
Z posixpath.pyc
Z pre.pyc
Z quopri.pyc
Z random.pyc
Z re.pyc
Z repr.pyc
Z rfc822.pyc
Z sgmllib.pyc
Z socket.pyc
Z sre.pyc
Z sre_compile.pyc
Z sre_constants.pyc
Z sre_parse.pyc
Z stat.pyc
Z string.pyc
Z tempfile.pyc
Z types.pyc
Z urllib.pyc
Z urlparse.pyc
Z uu.pyc
Z whichdb.pyc
Z whrandom.pyc
Z xml/
Z xml/__init__.pyc
Z xml/dom/
Z xml/dom/__init__.pyc
Z xml/dom/minidom.pyc
Z xml/dom/pulldom.pyc
Z xml/parsers/
Z xml/parsers/__init__.pyc
Z xml/parsers/expat.pyc
Z xml/sax/
Z xml/sax/__init__.pyc
Z xml/sax/_exceptions.pyc
Z xml/sax/expatreader.pyc
Z xml/sax/handler.pyc
Z xml/sax/saxutils.pyc
Z xml/sax/xmlreader.pyc
Z xmllib.pyc
------------------------------------------
F PyWinTypes%(winver)s.dll
F _socket.pyd
F _sre.pyd
F _winreg.pyd
F pyexpat.pyd
F python%(winver)s.dll
F sgmlop.pyd
F test_sax.exe
F win32api.pyd
F xmlparse.dll
F xmltok.dll
++++++++++++++++++++++++++++++++++++++++++
""")


TEST(r"""
>>> build('test_popen', args=['-e', 'win32api'])
Z Scripts.py2exe/
Z Scripts.py2exe/__main__.py
Z Scripts.py2exe/support.py
Z UserDict.pyc
Z copy.pyc
Z copy_reg.pyc
Z dospath.pyc
Z imputil.pyc
Z macpath.pyc
Z ntpath.pyc
Z os.pyc
Z popen2.pyc
Z posixpath.pyc
Z pre.pyc
Z re.pyc
Z repr.pyc
Z sre.pyc
Z sre_compile.pyc
Z sre_constants.pyc
Z sre_parse.pyc
Z stat.pyc
Z string.pyc
Z tempfile.pyc
Z types.pyc
------------------------------------------
F _sre.pyd
F python%(winver)s.dll
F test_popen.exe
++++++++++++++++++++++++++++++++++++++++++
""")


TEST(r"""
>>> build('test_system', args=['-e', 'win32api'])
Z Scripts.py2exe/
Z Scripts.py2exe/__main__.py
Z Scripts.py2exe/support.py
Z UserDict.pyc
Z copy.pyc
Z copy_reg.pyc
Z dospath.pyc
Z imputil.pyc
Z macpath.pyc
Z ntpath.pyc
Z os.pyc
Z popen2.pyc
Z posixpath.pyc
Z pre.pyc
Z re.pyc
Z repr.pyc
Z sre.pyc
Z sre_compile.pyc
Z sre_constants.pyc
Z sre_parse.pyc
Z stat.pyc
Z string.pyc
Z tempfile.pyc
Z types.pyc
------------------------------------------
F _sre.pyd
F python%(winver)s.dll
F test_system.exe
++++++++++++++++++++++++++++++++++++++++++
""")

try:
    import Numeric
except ImportError:
    print "Numeric not tested"
else:
    TEST("""
>>> build('test_numeric')
Z Scripts.py2exe/
Z Scripts.py2exe/__main__.py
Z Scripts.py2exe/support.py
Z imputil.pyc
------------------------------------------
F _numpy.pyd
F multiarray.pyd
F python%(winver)s.dll
F test_numeric.exe
++++++++++++++++++++++++++++++++++++++++++
""")

try:
    import win32ui
    import dde
except ImportError:
    print "dde not tested"
else:
    TEST("""
>>> build('test_dde')
Z Scripts.py2exe/
Z Scripts.py2exe/__main__.py
Z Scripts.py2exe/support.py
Z imputil.pyc
------------------------------------------
F PyWinTypes%(winver)s.dll
F dde.pyd
F python%(winver)s.dll
F test_dde.exe
F win32ui.pyd
++++++++++++++++++++++++++++++++++++++++++
""")

try:
    import win32api
except ImportError:
    print "win32 not tested"
else:
    TEST("""
>>> build('win32')
Z Scripts.py2exe/
Z Scripts.py2exe/__main__.py
Z Scripts.py2exe/support.py
Z imputil.pyc
Z win32com/
Z win32com/__init__.pyc
------------------------------------------
F PyWinTypes%(winver)s.dll
F python%(winver)s.dll
F win32.exe
F win32api.pyd
++++++++++++++++++++++++++++++++++++++++++
""")


try:
    import Tkinter
except ImportError:
    print "Tkinter not tested"
else:
    TEST("""
>>> build('test_hanoi', args=['-e', 'win32api'])
Z FixTk.pyc
Z Scripts.py2exe/
Z Scripts.py2exe/__main__.py
Z Scripts.py2exe/support.py
Z Tkconstants.pyc
Z Tkinter.pyc
Z UserDict.pyc
Z copy.pyc
Z copy_reg.pyc
Z dospath.pyc
Z imputil.pyc
Z linecache.pyc
Z macpath.pyc
Z ntpath.pyc
Z os.pyc
Z popen2.pyc
Z posixpath.pyc
Z pre.pyc
Z re.pyc
Z repr.pyc
Z sre.pyc
Z sre_compile.pyc
Z sre_constants.pyc
Z sre_parse.pyc
Z stat.pyc
Z string.pyc
Z tempfile.pyc
Z traceback.pyc
Z types.pyc
------------------------------------------
F _sre.pyd
F _tkinter.pyd
F python%(winver)s.dll
F tcl
F tcl83.dll
F test_hanoi.exe
F tk83.dll
++++++++++++++++++++++++++++++++++++++++++
""")


try:
    import wxPython
except ImportError:
    print "wxPython not tested"
else:
    TEST("""
>>> build('test_wx', args=['-e', 'win32api'])
Z Scripts.py2exe/
Z Scripts.py2exe/__main__.py
Z Scripts.py2exe/support.py
Z UserDict.pyc
Z copy.pyc
Z copy_reg.pyc
Z dospath.pyc
Z imputil.pyc
Z locale.pyc
Z macpath.pyc
Z ntpath.pyc
Z os.pyc
Z popen2.pyc
Z posixpath.pyc
Z pre.pyc
Z re.pyc
Z repr.pyc
Z sre.pyc
Z sre_compile.pyc
Z sre_constants.pyc
Z sre_parse.pyc
Z stat.pyc
Z string.pyc
Z tempfile.pyc
Z types.pyc
Z wxPython/
Z wxPython/__init__.pyc
Z wxPython/__version__.pyc
Z wxPython/clip_dnd.pyc
Z wxPython/cmndlgs.pyc
Z wxPython/controls.pyc
Z wxPython/controls2.pyc
Z wxPython/events.pyc
Z wxPython/filesys.pyc
Z wxPython/frames.pyc
Z wxPython/gdi.pyc
Z wxPython/image.pyc
Z wxPython/mdi.pyc
Z wxPython/misc.pyc
Z wxPython/misc2.pyc
Z wxPython/printfw.pyc
Z wxPython/sizers.pyc
Z wxPython/stattool.pyc
Z wxPython/streams.pyc
Z wxPython/utils.pyc
Z wxPython/windows.pyc
Z wxPython/windows2.pyc
Z wxPython/windows3.pyc
Z wxPython/wx.pyc
------------------------------------------
F _sre.pyd
F python%(winver)s.dll
F test_wx.exe
F utilsc.pyd
F wxc.pyd
F wxmsw232.dll
++++++++++++++++++++++++++++++++++++++++++
""")

TEST("""
>>> build('test_import')
Z Scripts.py2exe/
Z Scripts.py2exe/__main__.py
Z Scripts.py2exe/support.py
Z imputil.pyc
------------------------------------------
F python%(winver)s.dll
F test_import.exe
++++++++++++++++++++++++++++++++++++++++++
""")

def expand(str):
    return str % { 'winver': string.join(string.split(sys.winver, '.'), '') }

__doc__ = string.join(map(expand, tests))

from distutils.core import setup
from distutils.dir_util import remove_tree
import py2exe

class NullWriter:
    def write(self, text):
        pass

def check_contents(name, direct):
    from zipfile import ZipFile
    zf = ZipFile(os.path.join("dist", name, name+'.exe'))
    contents = zf.namelist()
    contents.sort()
    try:
        contents.remove("__future__.pyc")
    except ValueError:
        pass
    for item in contents:
        print "Z", item
    print "-" * 42
    files = os.listdir(os.path.join('dist', name))
    files.sort()
    if sys.winver == '1.5':
        files.remove("exceptions.pyc")
    for item in files:
        print "F", item
    print "+" * 42

def build(script, data_files=None, args=()):
##    sys.stderr.write("(Building %s)\n" % script)
    direct, name = os.path.split(script)
    old_sysargv = sys.argv
    sys.argv = ['', '-q', 'py2exe'] + list(args)
    old_stderr = sys.stderr
    sys.stderr = sys.stdout
    if data_files is not None:
        setup(name=name, scripts=[script + '.py'], data_files=data_files, version='0')
    else:
        setup(name=name, scripts=[script + '.py'], version='0')
    sys.stderr = old_stderr
    sys.argv = old_sysargv
    check_contents(name, direct)

def _test():
    print "Removing old directories"
    if os.path.exists("build"):
        remove_tree("build")
    if os.path.exists("dist"):
        remove_tree("dist")
    print "Running tests"
    import doctest, test_py2exe
    result = doctest.testmod(test_py2exe)
    print "Done"

if __name__ == '__main__':
    print
    _test()

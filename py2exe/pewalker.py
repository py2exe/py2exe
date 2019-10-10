#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""
pewalker
Methods used to determine the libraries linked by binary files (e.g. .pyd and .dll)

This file is distributed under the terms of the GNU General Public License v2,
see GPL2-License.txt.

"""
import pefile

def convert_dll_name_to_str(dll_name):
    """
    Convert dll names from 'bytes' to 'str'.
    Latest pefile returns type 'bytes'.
    :param dll_name:
    :return:
    """
    if isinstance(dll_name, bytes):
        return str(dll_name, encoding='UTF-8')
    else:
        return dll_name

def getImports(pth):
    """
    Find the binary dependencies of PTH.
    This implementation walks through the PE header
    and uses library pefile for that and supports
    32/64bit Windows
    """
    dlls = set()
    # By default library pefile parses all PE information.
    # We are only interested in the list of dependent dlls.
    # Performance is improved by reading only needed information.
    # https://code.google.com/p/pefile/wiki/UsageExamples

    pe = pefile.PE(pth, fast_load=True)
    pe.parse_data_directories(directories=[
        pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],
        pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT'],
        ],
        forwarded_exports_only=True,
        import_dllnames_only=True,
        )

    # Some libraries have no other binary dependencies. Use empty list
    # in that case. Otherwise pefile would return None.
    # e.g. C:\windows\system32\kernel32.dll on Wine
    for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
        dll_str = convert_dll_name_to_str(entry.dll)
        dlls.add(dll_str)

    # We must also read the exports table to find forwarded symbols:
    # http://blogs.msdn.com/b/oldnewthing/archive/2006/07/19/671238.aspx
    exportSymbols = getattr(pe, 'DIRECTORY_ENTRY_EXPORT', None)
    if exportSymbols:
        for sym in exportSymbols.symbols:
            if sym.forwarder is not None:
                # sym.forwarder is a bytes object. Convert it to a string.
                forwarder = convert_dll_name_to_str(sym.forwarder)
                # sym.forwarder is for example 'KERNEL32.EnterCriticalSection'
                dll, _ = forwarder.split('.')
                dlls.add(dll + ".dll")

    pe.close()
    return dlls

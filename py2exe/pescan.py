#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""
Methods used to determine the libraries linked by binary files (e.g. .pyd and .dll)

This work was derived from code originally licensed under the MIT license and owned by:
Copyright (c) 2004-2019 Ero Carrera.
Copyright (C) 2016 Deloitte Argentina.

"""

import pefile

def decode_bytes_to_string(name):
    try:
        r = name.decode('utf-8')
    except AttributeError:
        r = name
    return r

def find_loaded_dlls(path):

    dllset = set()

    # https://github.com/erocarrera/pefile/blob/wiki/UsageExamples.md#dumping-all-the-information-1
    # https://github.com/erocarrera/pefile/blob/master/pefile.py#L2495
    pe = pefile.PE(path, fast_load=True)
    pe.parse_data_directories(directories=[
        pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],
        pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT'],
        ],
        forwarded_exports_only=True,
        import_dllnames_only=True,
        )

    # https://github.com/codexgigassys/codex-backend/blob/master/src/Modules/PEFileModule.py
    try:
        imports = pe.DIRECTORY_ENTRY_IMPORT
    except AttributeError:
        imports = []

    for entry in imports:
        dll_str = decode_bytes_to_string(entry.dll)
        dllset.add(dll_str)

    # https://github.com/codexgigassys/codex-backend/blob/master/src/PlugIns/PE/ExportsPlug.py
    try:
        exports = pe.DIRECTORY_ENTRY_EXPORT
    except AttributeError:
        exports = None

    if exports is not None:
        for symbol in exports.symbols:
            if symbol.forwarder is not None:
                forwarder_str = decode_bytes_to_string(symbol.forwarder)
                basename = forwarder_str.split('.')[0]
                dllname = basename + ".dll"
                dllset.add(dllname)

    pe.close()

    return dllset

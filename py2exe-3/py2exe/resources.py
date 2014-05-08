#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""resources for py3exe
"""
import collections
import contextlib
import ctypes

from . import _wapi

@contextlib.contextmanager
def UpdateResources(filename, *, delete_existing=False):
    """A contextmanager which will update the resources in a Windows
    executable file.

    Returns a ResourceWriter object that has methods to add resource
    types.
    """
    hrscr = _wapi.BeginUpdateResourceW(filename, delete_existing)
    resource_writer = ResourceWriter(hrscr, filename)
    yield resource_writer
    resource_writer.flush()
    _wapi.EndUpdateResourceW(hrscr, False)
    # XXX We should update the file checksum here...


class ResourceWriter(object):
    def __init__(self, hrscr, filename):
        self._hrscr = hrscr
        self._filename = filename
        self._strings = {}

    def add(self, *, type, name, value, langid=0):
        """Write a resource to the exefile.
        <type> is typically a RT_xxx value.
        <name> can be a string or an integer.
        <value> is a byte string containing the resource data.
        """
        # I use keyword only args when I cannot remember the order of
        # positional arguments ;-)
        try:
            _wapi.UpdateResourceW(self._hrscr,
                                  _wapi.LPCWSTR(type),
                                  _wapi.LPCWSTR(name),
                                  langid, # wLanguage
                                  value,
                                  len(value))
        except WindowsError as details:
            raise WindowsError(details) from None

    def add_string(self, key, value):
        """Add a string to the string resource.  The strings will be
        buffered until flush() is called.

        Note: flush is called automatically in the UpdateResource
        context manager.
        """
        # Should we be able to specify a langid here? (see below)
        self._strings[key] = value

    def flush(self):
        """Flush all buffered data."""
        # Strings in the string resources are grouped in groups of 16.
        groups = collections.defaultdict(dict)
        for i in sorted(self._strings):
            sectnum, tabnum = divmod(i, 16)
            table = groups[sectnum+1]
            table[tabnum] = self._strings[i]

        # Collect the strings in each group, write them to a w_char_t
        # buffer prepended by the length and add them as RT_STRING
        # resource.
        for key, strings in groups.items():
            data = b""
            for i in range(16):
                text = strings.get(i, "")
                # Is it a performance problem to create a separate
                # structure for each group?
                class Entry(ctypes.Structure):
                    _fields_ = [("len", ctypes.c_ushort),
                                ("text", ctypes.c_wchar * len(text))]
                entry = Entry(len(text), text)
                data += memoryview(entry).tobytes()
            self.add(type=_wapi.RT_STRING, name=key, value=data,
                     langid=0x04b00409) # US english

        self._strings = {}

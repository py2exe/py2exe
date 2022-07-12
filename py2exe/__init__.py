#!/usr/bin/python3,3
# -*- coding: utf-8 -*-
"""py2exe package
"""
import setuptools

from .version import __version__

class Distribution(setuptools.Distribution):
    """Distribution with support for executables."""

    def __init__(self, attrs):
        self._create_var("console", attrs)
        self._create_var("windows", attrs)

        if not "zipfile" in attrs:
            attrs["zipfile"] = "library.zip"
        self._create_var("zipfile", attrs)

        super().__init__(attrs)

    def _create_var(self, name, attrs):
        value = attrs.get(name, None)
        setattr(self, name, value)

def setup(**attrs):
    attrs.setdefault("distclass", Distribution)
    setuptools.setup(**attrs)

setup.__doc__ = setuptools.setup.__doc__

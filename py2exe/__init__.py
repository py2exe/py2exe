#!/usr/bin/python3,3
# -*- coding: utf-8 -*-
"""py2exe package
"""
import setuptools

from .version import __version__

def setup(**attrs):
    if not "zipfile" in attrs:
        attrs["zipfile"] = "library.zip"
    setuptools.setup(**attrs)

setup.__doc__ = setuptools.setup.__doc__

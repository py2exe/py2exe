#!/usr/bin/python3,3
# -*- coding: utf-8 -*-
"""py2exe package
"""
__version__ = '0.9.4.0'

from .patch_distutils import patch_distutils

patch_distutils()

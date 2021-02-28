#!/usr/bin/python3,3
# -*- coding: utf-8 -*-
"""py2exe package
"""

from .version import __version__

from .patch_distutils import patch_distutils

patch_distutils()

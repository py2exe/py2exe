#!/usr/bin/python3,3
# -*- coding: utf-8 -*-

import sys

class Log():
    """Dummy class to keep logging even after `CPython.logging`
    har been tampered by `setuptools.logging.configure`."""
    def debug(self, msg):
        sys.stdout.write('[DEBUG] ' + msg + '\n')

    def info(self, msg):
        sys.stdout.write('[INFO] ' + msg + '\n')

    def warning(self, msg):
        sys.stdout.write('[WARNING] ' + msg + '\n')

    def error(self, msg):
        sys.stderr.write('[ERROR] ' + msg + '\n')

#!/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

from functools import wraps
import logging
import sys
import traceback

logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

def catch_errors(fn):
    """Catch all sort of exceptions, print them, print the stacktrace.

    This is helpful to refactor try/except blocks.
    I.e:

    ```
    def method():
        try:
            foo._title(url)
        except Exception as e:
            log.debug("error at ...")
    ```
    becomes
    ```
    @catch_errors
    def method():
        foo._title()
    ```
    """

    @wraps(fn)  # juste to preserve the name of the decorated fn.
    def handler(inst, arg):
        try:
            return fn(inst, arg)
        except Exception as e:
            log.error("Error at method {}: {}".format(fn.__name__, e))
            log.error("for search: {}".format(inst.query))
            # The traceback must point to its origin, not to this decorator:
            exc_type, exc_instance, exc_traceback = sys.exc_info()
            log.error("".join(traceback.format_tb(exc_traceback)))

    return handler

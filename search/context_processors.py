# -*- coding: utf-8 -*-
# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
import subprocess

from django.conf import settings

ABELUJO_VERSION = None

def get_abelujo_version():
    """
    Read Abelujo's version from its git tag on startup.

    Return: a string, like '0.69-283-g35f72d4b\n'.
    """
    version = None
    try:
        version = subprocess.check_output("git describe --always --tags", shell=True)
        global ABELUJO_VERSION
        ABELUJO_VERSION = version
    except Exception as e:
        print("Could not get abelujo git tag version: \n {}".format(e))

get_abelujo_version()


def global_settings(request):
    # return any necessary values
    return {
        'FEATURE_EXCLUDE_FOR_WEBSITE': settings.FEATURE_EXCLUDE_FOR_WEBSITE,
        'ABELUJO_VERSION': ABELUJO_VERSION,
    }

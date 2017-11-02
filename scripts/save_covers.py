#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2017 The Abelujo Developers
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

import json
import os
import yaml

from tqdm import tqdm

from search.models.models import Card
from abelujo.settings import MEDIA_ROOT

"""
Save all covers on disk.

Run with the runscript management command.

Usage:

./manage.py runscript save_covers
"""
def run(*args):

    covdir = os.path.join(MEDIA_ROOT, "covers")
    l1 = len(os.listdir(covdir))
    print "Covers in directory: {}".format(l1)
    for card in Card.objects.all():
        print "Saving cover of card {}...".format(card.id)
        card.save_cover()

    l2 = len(os.listdir(covdir))
    print "Covers in directory: {}.\n-----\n{} covers created".format(l2, l2 - l1)

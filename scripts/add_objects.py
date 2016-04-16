
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

import json
import os
import yaml

from tqdm import tqdm

from search.models.models import Card
from search.models.models import CardType
from search.models.models import Shelf
from search.models.models import Place
from search.models.models import Preferences

"""Add and create objects to the database, from a yaml file.

Run with the runscript management command.

Usage:

./manage.py runscript add_objects --script-args=scripts/shelfs_fr.yaml
"""
def run(*args):
    """Define a yaml:
    - model: name of the model
    - from_string: string with space-separated names of objects to create.

    """

    def add_object(model, name):
        try:
            obj, created = model.objects.get_or_create(name=name)
        except Exception as e:
            print e

    src = args[0]
    with open(src, "r") as f:
        data = yaml.load(f.read())

    names = data.get('from_string').split(" ")
    print "We got: "
    print names
    model = globals()[data['model']]
    print "Adding objects to {}...".format(data['model'])
    for name in tqdm(names):
        add_object(model, name)

    print "Done."

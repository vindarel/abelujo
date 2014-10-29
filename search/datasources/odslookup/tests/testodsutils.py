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

import os
import sys
import unittest

common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
cdpp, _ = os.path.split(cdp)
sys.path.append(cdpp)

from odslookup.odsutils import translateAllKeys
from odslookup.odsutils import keysEqualValues

class testOdsUtils(unittest.TestCase):

    def setUp(self):
        self.data = [
            {"titre": "un titre",
             "auteur": "un auteur",
             "editeur": "un éditeur",
             },
            ]
        pass

    def tearDown(self):
        pass

    def testTranslateAllKeys(self):
        tr = translateAllKeys(self.data)
        self.assertTrue(tr[0].has_key("title"))
        self.assertTrue(tr[0].has_key("publisher"), "no publisher key after translation.")

    def testKeysEqualValues(self):
        self.assertFalse(keysEqualValues(self.data[0]))
        self.assertTrue(keysEqualValues({"foo": "foo", "éditeur": "éditeur"}))
        self.assertTrue(keysEqualValues({}))

if __name__ == '__main__':
    unittest.main()

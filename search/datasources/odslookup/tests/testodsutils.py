#!/bin/env python
# -*- coding: utf-8 -*-

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

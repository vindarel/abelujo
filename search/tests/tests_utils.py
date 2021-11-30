#!/bin/env python
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

from django.test import TestCase

from search.models.common import ALERT_ERROR
from search.models.common import ALERT_INFO
from search.models.common import ALERT_SUCCESS

from search.models.utils import Messages, is_isbn, split_query, isbns_from_query, is_truthy, toIntOrFloat
from search.models.utils import parent_theme_name

from search import views_utils

class TestMessages(TestCase):

    def setUp(self):
        pass

    def test_messages(self):
        msgs = Messages()
        msgs.add_success('yes')
        self.assertEqual(msgs.status, ALERT_SUCCESS)
        self.assertEqual(msgs.to_list()['status'], ALERT_SUCCESS)
        self.assertEqual(msgs.msgs[0]['message'], 'yes')

    def test_messages_statuses(self):
        msgs = Messages()
        msgs.add_success('yes')
        msgs.add_error('no')
        # global status is updated,
        self.assertEqual(msgs.status, ALERT_ERROR)
        # yet we can set it manually.
        msgs.status = ALERT_SUCCESS
        self.assertEqual(msgs.status, ALERT_SUCCESS)

    def test_messages_merge(self):
        msgs = Messages()
        msgs.add_success('yes')
        mm = Messages()
        mm.add_error('no')

        msgs.merge(mm)
        self.assertEqual(msgs.status, ALERT_ERROR)

    def test_messages_append(self):
        msgs = Messages()
        msgs.add_success('yes')
        mm = Messages()
        mm.add_info('mm')
        msgs.append(mm.msgs)
        self.assertEqual(len(msgs.msgs), 2)
        self.assertEqual(ALERT_INFO, msgs.status)


class TestUtils(TestCase):

    def setUp(self):
        pass

    def test_is_isbn(self):
        self.assertEqual("9782918059363", is_isbn("9782918059363"))
        self.assertFalse(is_isbn("9782918059363; 9782918059363; RST, 978"))
        self.assertEqual(3, len(split_query("9782918059363; 9782918059363; RST, 978")))
        self.assertEqual(3, len(split_query("9782918059363, 9782918059363, RST 978")))
        self.assertEqual(3, len(split_query("9782918059363 9782918059363 978_RST")))

        self.assertEqual(2, len(isbns_from_query("9782918059363 9782918059363 978_RST")))
        self.assertEqual(2, len(isbns_from_query("9782918059363, 9782918059363, 978_RST")))

    def test_is_truthy(self):
        self.assertFalse(is_truthy("false"))
        self.assertFalse(is_truthy("0"))
        self.assertFalse(is_truthy("undefined"))
        self.assertFalse(is_truthy(False))
        self.assertFalse(is_truthy(None))

        self.assertTrue(is_truthy("true"))
        self.assertTrue(is_truthy("1"))
        self.assertTrue(is_truthy("yes"))

    def test_toIntOrFloat(self):
        self.assertEqual(1, toIntOrFloat("1"))
        self.assertEqual(1.10, toIntOrFloat("1.10"))
        self.assertEqual(4.0, toIntOrFloat("4.[Filtered]"))

    def test_parent_theme_name(self):
        self.assertTrue(parent_theme_name(3781).startswith('Bandes'))
        res = parent_theme_name("3008")
        self.assertTrue(res.startswith('Manuels'))
        res = parent_theme_name("3001")
        self.assertTrue(res.startswith('SCOLAIRE'))


class TestViewUtils(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_extract_all_isbns_quantities(self):
        # only ISBN
        inputrows = ["// comment 1",
                     "// comment 1",
                     "//",
                     "// comment 3",
                     "9782918059363",
                     ]
        rows, msgs = views_utils.extract_all_isbns_quantities(inputrows)
        self.assertEqual(rows, [["9782918059363", 1]])

        # ISBN;qté
        inputrows = ["// comment 1",
                     "// comment 1",
                     "//",
                     "// comment 3",
                     " 9782918059363 ; 99  ",
                     "9782918059363;77",
                     ]
        rows, msgs = views_utils.extract_all_isbns_quantities(inputrows)
        self.assertEqual(rows, [["9782918059363", 99],
                                ["9782918059363", 77]])

        # ISBN; bad qty
        inputrows = ["// comment 1",
                     "// comment 1",
                     "//",
                     "// comment 3",
                     "9782918059363;TRASH",
                     ]
        rows, msgs = views_utils.extract_all_isbns_quantities(inputrows)
        self.assertFalse(rows)
        self.assertTrue(len(msgs))

        # ISBN + space + qty
        inputrows = ["// comment 1",
                     "// comment 1",
                     "//",
                     "// comment 3",
                     "9782918059363  99  ",
                     "  9782918059363   77    ",
                     ]
        rows, msgs = views_utils.extract_all_isbns_quantities(inputrows)
        self.assertEqual(rows, [["9782918059363", 99],
                                ["9782918059363", 77]])

        # With \t instead of space (most real world)
        inputrows = """ 9782918059363	99
9782918059363	77
        """
        inputrows = inputrows.strip().split('\n')

        rows, msgs = views_utils.extract_all_isbns_quantities(inputrows)
        self.assertEqual(rows, [["9782918059363", 99],
                                ["9782918059363", 77]])

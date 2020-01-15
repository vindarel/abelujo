#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2019 The Abelujo Developers
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

from django.test import TestCase

from search.models.common import ALERT_ERROR
from search.models.common import ALERT_INFO
from search.models.common import ALERT_SUCCESS

from search.models.utils import Messages, is_isbn, split_query, isbns_from_query

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

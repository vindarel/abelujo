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

from django.test import TestCase

from search import mailer
# from search.models import Reservation

from tests_api import CardFactory


class TestMailer(TestCase):

    def setUp(self):
        self.card = CardFactory.create()

    def tearDown(self):
        pass

    def test_body(self):
        body = mailer.generate_body_for_client_command_confirmation("10 €", [self.card])
        self.assertTrue(body)

    def notest_send_mail(self):
        mailer.send_command_confirmation([self.card])

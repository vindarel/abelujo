#!/bin/bash
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

# add end to end tests manually. We want them to run periodically
# and independently from the unit tests.
# To be much improved: we want a test suite and its report, async.

python datasources/all/discogs/discogsConnectorLiveTest.py
python datasources/frFR/chapitre/tests/e2e/chapitreLiveTest.py

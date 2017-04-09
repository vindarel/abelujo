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

"""
Huey asynchronous tasks.
"""

import logging
from huey.contrib.djhuey import db_task

from models import Inventory, InventoryCommand

logging.basicConfig(format='%(levelname)s [%(name)s:%(lineno)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

@db_task()
def inventory_apply_task(pk):
    log.info("Starting task inventory apply of inventory {}".format(pk))
    status, alerts = Inventory.apply_inventory(pk)
    log.info("Task inventory apply finished for inventory {}".format(pk))


@db_task()
def command_inventory_apply_task(pk):
    log.info("Starting task inventory apply of InventoryCommand {}".format(pk))
    status, alerts = InventoryCommand.apply_inventory(pk)  # add the quantity to the stock.
    log.info("Task inventory apply finished for InventoryCommand {}".format(pk))

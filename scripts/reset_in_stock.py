#!/usr/bin/env python
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

from tqdm import tqdm

from search.models.models import Card
from search.models.models import Inventory

def run(*args):
    """Reset the in_stock Card property. It was set to True by default, it
    should be False. So each card that was bought once or added from
    an inventory should be to True.
    """

    yes_answers = ["y", "Y", "o", "O", ""]
    go_all_cards = raw_input("Go with all cards ? [Y/n]")
    go_inventories = raw_input("Go with cards applied from inventories ? [Y/n]")

    if go_all_cards in yes_answers:
        print("Setting all cards to not in stock...")
        for card in tqdm(Card.objects.all()):
            card.in_stock = False
            card.save()

    if go_inventories in yes_answers:
        print("Registering cards applied from inventories...")
        for inv in tqdm(Inventory.objects.filter(applied=True)):
            print("Going with inv {}".format(inv.name))
            for card_set in inv.inventorycopies_set.all():
                card_set.card.in_stock = True
                card_set.card.save()

    print("All done.")

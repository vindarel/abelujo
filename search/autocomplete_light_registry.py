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
import autocomplete_light
from models import Card

# This will generate a CardAutocomplete class
class CardAutocomplete(autocomplete_light.AutocompleteModelBase):
    # Just like in ModelAdmin.search_fields
    search_fields=['title', 'authors.objects.all()'],
    # This will actually html attribute data-placeholder which will set
    # javascript attribute widget.autocomplete.placeholder.
    autocomplete_js_attributes={'placeholder': 'ean',}
    # autocomplete_template = 'your_autocomplete_box.html'

    def choices_for_request(self):
        q = self.request.GET['q']
        cards = Card.search(q)
        # log cards
        return cards

autocomplete_light.register(Card, CardAutocomplete)

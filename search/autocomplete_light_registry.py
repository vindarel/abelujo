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

import autocomplete_light
# from models import Person
from models import Card

# This will generate a PersonAutocomplete class
autocomplete_light.register(Card,
    # Just like in ModelAdmin.search_fields
    search_fields=['title', ],
    # This will actually html attribute data-placeholder which will set
    # javascript attribute widget.autocomplete.placeholder.
    # autocomplete_js_attributes={'placeholder': 'Other model name ?',},
)

# equivalent:
# class CardAutocomplete(autocomplete_light.AutocompleteModelBase):
    # search_fields = ["^title",]

# autocomplete_light.register(Card, CardAutocomplete)

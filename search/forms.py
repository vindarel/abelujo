# -*- coding: utf-8 -*-
# Copyright 2014 - 2020 The Abelujo Developers
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

import json

from django import forms
from django.forms.widgets import TextInput
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as __  # in Meta and model fields.

import models
from search.models import Card
from search.models import Preferences

from search.models import Bill
from search.models import Deposit
from search.models import Distributor
from search.models import Place
from search.models import Publisher

from search.models.utils import get_logger

log = get_logger()

MAX_COPIES_ADDITIONS = 10000  # maximum of copies to add at once

PAYMENT_MEANS = [
    (1, "cash"),
    (2, "credit card"),
    (3, "cheque"),
    (4, "gift"),
    (5, "lost"),
]

CURRENCY_CHOICES = [
    ('euro', '€'),
    ('chf', 'CHF'),
]

class MyNumberInput(TextInput):
    # render an IntegerField with a "number" html5 widget, not text.
    input_type = 'number'


def get_distributor_choices():
    dists = [(dist.id, dist.name) for dist in Distributor.objects.all()]
    pubs = [(pub.id, pub.name) for pub in Publisher.objects.all()]
    choices = [(_(u"Distributors"),
                dists),
               (_(u"Publishers"),
                pubs)]
    return choices


def validate_and_get_discounts(data):
    """
    data: string, percentages separated by ;
    """
    if not data.strip():
        return []
    data = data.replace(',', '.')
    str_discounts = data.split(';')
    discounts = []
    for it in str_discounts:
        try:
            discounts.append(float(it))
        except Exception:
            log.debug("Discounts form not valid: {}".format(data))
            raise forms.ValidationError(_("Bad discounts: enter percentages separated by ';'."))

    return discounts


class PrefsForm(forms.Form):
    # bookshop_name = forms.CharField(label='Your bookshop name', max_length=100)
    # vat_book = forms.FloatField(label='VAT of books')
    CURRENCY_CHOICES = [
        ('euro', '€'),
        ('chf', 'CHF'),
    ]
    default_currency = forms.ChoiceField(choices=CURRENCY_CHOICES, required=False)
    #: Discounts we are allowed to apply for a sell.
    #: Char field, percentages separated by ;
    sell_discounts = forms.CharField(
        max_length=100,
        required=False,
        # label='Hello',
        widget=forms.TextInput(),
        validators=[validate_and_get_discounts],
    )

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        # Not on form validation.
        if not args:
            prefs = Preferences.objects.first()
            currency = 'euro'
            try:
                currency = json.loads(prefs.others)['default_currency']
            except Exception as e:
                log.warn(u"Preferences: could not load the default currency (will use euro): {}.".format(e))

            # Change the default presentation: show € in we have CHF.
            if currency and currency == 'chf':
                self.CURRENCY_CHOICES = [
                    ('chf', 'CHF'),
                    ('euro', '€'),
                ]
            else:
                self.CURRENCY_CHOICES = [
                    ('euro', '€'),
                    ('chf', 'CHF'),
                ]

            self.fields['default_currency'] = forms.ChoiceField(choices=self.CURRENCY_CHOICES)

            current_discounts = ''
            sell_discounts = None
            if prefs.others and 'sell_discounts' in prefs.others:
                try:
                    sell_discounts = json.loads(prefs.others)['sell_discounts']
                except Exception:
                    pass
            if sell_discounts:
                current_discounts = "; ".join(["{}".format(it) for it in sell_discounts])
                self.fields['sell_discounts'] = forms.CharField(
                    max_length=100,
                    required=False,
                    # label='Hello',
                    widget=forms.TextInput(attrs={'placeholder': current_discounts}),
                    validators=[validate_and_get_discounts],
                )

class AddForm(forms.Form):
    """The form populated when the user clicks on "add this card"."""
    # The search is saved to the session so we need to get the element we want: hence the for counter.
    # We couldn't find how to populate its value (which is {{ forloop.counter0 }})
    # without not writting it explicitely in the template.
    forloop_counter0 = forms.IntegerField(min_value=0,
                                          widget=forms.HiddenInput())

def get_places_choices():
    not_stands = Place.objects.filter(is_stand=False)
    preferences = Preferences.objects.first()
    ret = []
    if preferences:
        default_place = preferences.default_place
        ret = [(default_place.id, default_place.name)] + [(p.id, p.name) for p in not_stands
                                                          if not p.id == default_place.id]
    return ret

def get_suppliers_choices():
    res = Distributor.objects.order_by("-name").all()
    res = [(it.id, it.__repr__()) for it in res]
    return res

class DepositForm(forms.ModelForm):
    """Create a new deposit.
    """
    copies = forms.ModelMultipleChoiceField(Card.objects.all(), required=False)

    class Meta:
        model = Deposit
        fields = "__all__"
        # exclude = ["copies",]

class DepositAddCopiesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        pk = kwargs.pop('pk')
        super(self.__class__, self).__init__(*args, **kwargs)

        # Build fields depending on the deposit existing cards.
        dep = Deposit.objects.get(id=pk)
        cards = dep.copies()
        for card in cards:
            self.fields[str(card.id)] = forms.IntegerField(widget=MyNumberInput(
                attrs={'min': 0, 'max': MAX_COPIES_ADDITIONS,
                       'step': 1, 'value': 0,
                       'style': 'width: 70px'}),
                                                           label=card.title)


def get_deposits_choices():
    choices = [(depo.name, depo.name) for depo in Deposit.objects.all()]
    return choices

class AddToDepositForm(forms.Form):
    """When we view our stock, choose to add the card to a deposit.
    """
    deposit = forms.ChoiceField(choices=get_deposits_choices(),
                                label=_(u"Add to the deposit:"),
                                required=False)

def get_bills_choices():
    bills = Bill.objects.all()
    ret = [(0, "---")] + [(it.id, it.long_name) for it in bills]
    return ret
class CardMoveForm(forms.Form):
    """We want to create a field for each Place and Basket object

    This approch is too much work to create a simple form. We want to
    write our form directly in a template instead, using angularjs
    calls to an api to fetch the places and baskets.
    """
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        model = "Place"
        query = models.__dict__[model].objects.all()
        for obj in query:
            self.fields[obj.name] = forms.IntegerField(widget=MyNumberInput(
                attrs={'min': 0, 'max': MAX_COPIES_ADDITIONS,
                       'step': 1, 'value': 1,
                       'style': 'width: 70px'}))


class CardMove2BasketForm(forms.Form):
    # I don't like, but I now like it better than JS and api calls.
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        model = "Basket"
        query = models.__dict__[model].objects.all()
        for obj in query:
            self.fields[obj.name] = forms.IntegerField(widget=MyNumberInput(
                attrs={'min': 0, 'max': MAX_COPIES_ADDITIONS,
                       'step': 1, 'value': 0,
                       'style': 'width: 70px'}))


class CardMoveTypeForm(forms.Form):
    choices = [(1, "Pay these cards"),
               (2, "Add to a deposit"),
               (3, "Internal movement"),
    ]
    typ = forms.ChoiceField(choices=choices)


class BuyForm(forms.Form):
    payment = forms.ChoiceField(choices=PAYMENT_MEANS, label=_("Payment"))
    bill = forms.ChoiceField(choices=get_bills_choices(), label=_("Bill"))
    quantity = forms.FloatField(label=_("Quantity"))
    place = forms.ChoiceField(choices=get_places_choices(), label=_("Place"))


class MoveDepositForm(forms.Form):
    choices = forms.ChoiceField(choices=get_deposits_choices())


class CardPlacesAddForm(forms.Form):
    """
    Add exemplaries to some Places, from the Card view.
    """

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        for place in Place.objects.order_by("id").all():
            self.fields[place.id] = forms.IntegerField(required=False, label=place.name)


class MoveInternalForm(forms.Form):
    nb = forms.IntegerField(label=__("Quantity"))

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.fields['origin'] = forms.ChoiceField(choices=get_places_choices(),
                                                  label=__("origin"))
        self.fields['destination'] = forms.ChoiceField(choices=get_places_choices(),
                                                       label=__("destination"))


class SetSupplierForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.fields[_('supplier')] = forms.ChoiceField(choices=get_suppliers_choices())


class NewSupplierForm(forms.Form):
    name = forms.CharField()
    discount = forms.IntegerField(label=_("discount"))

# -*- coding: utf-8 -*-
# "currency" filter to print a price in €, CHF or other currency

import six

from django import template

from search.models import Preferences

register = template.Library()

"""
Usage:


``
{% load currencyfilter %}

  {{ price | currency }}
``

prints "20.00 €" or "CHF 20.00".
"""

@register.filter(name='currency')
def currencyfilter(price):
    if price is None:
        return ''

    if isinstance(price, six.string_types) or isinstance(price, six.text_type):
        try:
            price = int(price)
        except Exception:
            return ''

    currency = Preferences.default_currency
    try:
        if not currency:
            # Happens in tests, in bare bones setup.
            return '{:.2f} €'.format(price)
        if currency.lower() in ['chf', u'chf']:
            return 'CHF {:.2f}'.format(price)
        else:
            return '{:.2f} €'.format(price)
    except Exception:
        return '{:.2f}'.format(price)

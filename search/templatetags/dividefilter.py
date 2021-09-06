# -*- coding: utf-8 -*-
# Divide filter: substract numbers.

import six

from django import template

from search.models import Preferences

register = template.Library()

"""
Usage:


``
{% load dividefilter %}

  {{ 10 | div:5 }}
``

prints 2
"""

@register.filter(name='div')
def dividefilter(nb, divisor):
    if nb is None:
        return ''
    if divisor is 0:
        return nb

    return '{:.2f}'.format(nb / divisor)

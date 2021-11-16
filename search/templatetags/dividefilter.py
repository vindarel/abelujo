# -*- coding: utf-8 -*-
# Divide filter: substract numbers.

import six

from django import template

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
    if not nb:
        return ''

    if isinstance(nb, six.string_types) or isinstance(nb, six.text_type):
        nb = int(nb)
    if isinstance(divisor, six.string_types) or isinstance(divisor, six.text_type):
        divisor = int(divisor)

    if divisor is 0:
        return nb

    divisor = divisor / 1.0  # we want a float to get decimals. 100 -> 100.0
    return '{:.2f}'.format(nb / divisor)

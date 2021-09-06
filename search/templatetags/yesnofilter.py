# -*- coding: utf-8 -*-
# yesno: True means "yes"

import six

from django import template

from search.models import Preferences

register = template.Library()

"""
Usage:


``
{% load dividefilter %}

  {{ truthy_value | yes-no }}
``

prints "yes"
"""

@register.filter(name='yesno')
def yesnofilter(value):
    if value:
        return 'Oui'
    return 'Non'

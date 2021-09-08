# -*- coding: utf-8 -*-
# yesno: True means "yes"

from django import template

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

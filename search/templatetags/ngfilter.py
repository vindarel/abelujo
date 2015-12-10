# "ng" filter to let angularjs interpolate the variable, not django.

from django import template
from django.utils import safestring

register = template.Library()

"""
Usage:

in templates, use

``
{% load ngfilter %}

<div>
  {{ django_context_var }}
  {{ 'angularScopeVar' | ng }}
  {{ 'angularScopeFunction()' | ng }}
</div>
``

instead of {% verbatim %} {{ angularScopeVar }} {% endverbatim %}
"""

@register.filter(name='ng')
def Ngfilter(value):
    return safestring.mark_safe('{{%s}}' % value)

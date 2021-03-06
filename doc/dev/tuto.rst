Django tutorial
===============

Intermediate tables
-------------------

Goal: have a many to many relationship, like between a place and a
card, but specify some custom elements, like the number of copies.

See the Django doc: https://docs.djangoproject.com/en/1.5/topics/db/models/#intermediary-manytomany

So, we can create a Card and a Place as usual. But to access a Card
from a Place, we have to use the intermediate table, like this::

    self.place.placecopies_set.get(card=mycard)  # or all() or others, cf doc.

See:

* the relation card-place, card-basket, and their unit tests for usage
  examples (test_models.py).


Autocompletion in forms
-----------------------

Django forms are nice, but they get unusable when a select field has a
lot of inputs, like when we want to select a card among the few
thousands from our database.

We want some sort of autocompletion: we start typing a part of the
title of the form and we are displayed a nice list of matching
results.

We use `django-autocomplete-light <http://django-autocomplete-light.readthedocs.org/en/latest/>`_.

The app django-ajax-selects is similar but was more difficult to setup.

Another obvious solution is to set up a full featured MVC javascript
framework, like AngularJS, but a django app is simpler and quicker to
set up in simple cases.


Logging
-------

We define a default logger so than we can setup a logger with::

    import logging
    log = logging.getLogger(__name__)

and it will by default print verbose messages to the console (Django's
default is to a file). In `settings.py`, see the handler `console` and
the logger `""` to catch all the undefined ones.

https://docs.djangoproject.com/en/1.6/topics/logging/

http://www.miximum.fr/an-effective-logging-strategy-with-django.html

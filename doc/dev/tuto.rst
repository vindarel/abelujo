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

We used once `django-autocomplete-light
<http://django-autocomplete-light.readthedocs.org/en/latest/>`_. It
did the job well and was easy to setup, but we wanted more
features. We want the selection of a *select* to affect the results of
another one. For example, during the deposits creation, there is a
*select* for the distributor and another one for searching cards. So,
we want to search cards whose distributor is the one selected just
above. `django-autocomplete-light` could do it… with a lot of
javascript code. So it was the moment to choose our own javascript
framework.

The app django-ajax-selects is similar but was more difficult to setup.

Eventually we set up a full featured MVC javascript framework and we
chose AngularJS. We do the autocompletion stuff with `angular-ui's
typeahead <https://angular-ui.github.io/bootstrap/#/typeahead>`_.

Typeahead (ajax-based autocompletion) with AngularJS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As with Angular, there are html markup and javascript code to look at.

In `templates/search/deposits_create.jade <https://gitlab.com/vindarel/abelujo/blob/master/templates/search/deposits_create.jade#L55>`_.

In `static/js/app/controllers/controller.js <https://gitlab.com/vindarel/abelujo/blob/master/static/js/app/controllers/controller.js#L36>`_.


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

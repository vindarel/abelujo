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

Internationalization, translations
----------------------------------

Django provides tools to translate our application in different languages: https://docs.djangoproject.com/en/1.7/topics/i18n/translation/

In python code, we enclose the translatable strings in "_()" where _
is a shortcut for `ugettext`. The `gettext` family are unix tools.

In templates, we use `{% trans "foo" %}` tags, or `blocktrans` for
more complicated cases.

Note::

    The trans tag is in between quotes if the original string is ;)

Django also provides a facility to translate strings in our javascript
code. As explained in the docs, at our `base.jade` template we source
to a javascript script provided by Django that offers a `gettext`
function, and we include a `jsi18n` url which allows Django to ask for
translations.

There's a bit of `settings` too.

We chose the solution to select the language by prepending its prefixe
to every url (done automatically by Django).

To translate the app we need to do the above, then to create
translation files (`.po` files), to translate everything, and to
compile the translation files.

See our Makefile for `translation-` rules. To update all `.po` files
(from python, html, jade and js sources), run::

    make translation-files

To compile the translations and see them in the application, run::

    make translations-compile
    # a shortcut for django-admin compilemessages

To create a `.po` file for a new language, specify the `-l` (locale)::

    python manage.py makemessages -e py,html,jade -l en


See also how to translate urls, to pluralize nouns, to give context to
the translators, to manually get or set the language, etc.

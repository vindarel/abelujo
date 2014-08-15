Developer documentation
=======================


Autocompletion in forms
-----------------------

Django forms are nice, but they get unusable when a select field has a
lot of inputs, like when we want to select a card among the few
thousands from our database.

We want some sort of autocompletion: we start typing a part of the
title of the form and we are displayed a nice list of matching
results.

We use **django-autocomplete-light**: http://django-autocomplete-light.readthedocs.org/en/latest/

The app django-ajax-selects is similar but was more difficult to setup.

Another obvious solution is to set up a full featured MVC javascript
framework, like AngularJS, but we don't want to deal with that yet.

We have usable forms without the need to write a line of javascript,
and that's fine for now. We want to stay focused on the application
logic (we know all the burden that requires the affordmentioned
framework !).

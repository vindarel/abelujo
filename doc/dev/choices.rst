Technical choices
=================


Why AngularJS ?
---------------

`AngularJS <https://angularjs.org/>`_ is a Model-View-Controller
framework to build dynamic user interfaces. It does double-data
binding at its core.

Why not JQuery, Ember or <anothe popular JS framework> ?

Angular isn't comparable with JQuery. See the basics: https://angularjs.org/#the-basics

Why not a simple library that does double data binding (like view.js)
? Because we will use all the power of Angular (we need js functions
as controllers, unit tests, end to end tests, and the like).

Ember has a similar scope. But besides technical details, it appears
we already have significant experience with Angular.

Read our Angular crash course to learn how to add Angular to a Django
project, how to build everything, and how everything works.

Npm
---

The Node Package Manager. Install dependencies listed in
``package.json`` (it must be a valid json: no commentaries, beware
of trailing commas) and execute post-install actions.

Run::

    npm install

It installs ``gulp``, ``bower``, etc.

Post-actions:

- ``bower install`` (reading bower.json list of dependencies).

Todo: enable js tests: https://github.com/bearstech/cookiecutter-django-bootstrap-angular/blob/master/{{cookiecutter.project_name}}/package.json

Now a few words about npm libraries we use.

datejs
~~~~~~

http://www.datejs.com/2007/11/27/getting-started-with-datejs/

It enhances the javascript `Date` object with many useful methods. For
example, we can print a date to a given format with
`date.toString("yyyy-MM-dd")`. With bare javascript this isn't
possible (as cleanly).

Bower
-----

`Bower <http://bower.io/>`_ is a package manager (of js libraries) optimized for the
front-end. It uses a flat dependency-tree, requiring only one version
for each package. It requires nodejs, npm and git.

`django-bower <https://pypi.python.org/pypi/django-bower>`_ leverages
some actions to install bower packages.

Given some configuration into ``settings.py``, it provides a management
command to install packages in ``static/bower_components/``.::

    ./manage.py bower install

The list of requirements lies in ``settings.py`` into the variable ``BOWER_INSTALLED_APPS``.

Then we can add scripts in templates like:::

    {% load static %}
    <script type="text/javascript" src='{% static 'jquery/jquery.js' %}'></script>

django-bower VS gulpfile
~~~~~~~~~~~~~~~~~~~~~~~~

Gulp
----

`Gulp <https://github.com/gulpjs/gulp>`_ defines itself as the
streaming build system. We configure actions to:

- take all the installed JS libs in bower_components and concatenate them in one file;
- take all our own JS code and pass it through any transformer/code
  checker (linter) needed (coffee, jshint);
- concatenate all our JS code in one big JS file, so than we simply
  include one file in our templates and we have included our Angular app;
- do the same with custom CSS.

The defined actions are (see ``gulpfile.js``):

- ``gulp`` by default runs ``less`` and ``concat``
- ``gulp run``
- ``gulp watch``: auto browser reload.

LiveScript
----------

A browser understands javascript, so the front end of a web app must
be written in js. However, it is a very unconsistent language with
many pitfalls, and a bit of a pain to write because of its many
parenthesis and brackets, especially for a python developer.

Many alternatives exist and `LiveScript <http://livescript.net>`_ is a
fantastic one. It is a little language that transpiles to
javascript. It solves many inconsistencies of js, it doesn't get in
our way, it is indentation-aware like Python, it is very concise, it
greatly encourages functional programming and it has a good tooling
and community. See what's possible to do in very few lines of code
with its `prelude library <http://livescript.net/#prelude-ls>`_.

Livescript has many more to offer than other alternatives like
Coffeescript or RapydScript (the "pythonic" javascript).

Quick reference:

- functions are declared like in coffeescript with the arrow
  notation. They return the last expression by default, unless we
  declare the function with ``!->``, in which case we need to write the
  ``return`` statement.

  .. code-block:: coffeescript

     save = (arg) ->
         ...

- the ``do`` notation helps in many things, like creating dictionnaries (javascript objects)

  .. code-block:: coffeescript

     params = do
       card_id: $scope.card_id

- the functional methods are handy to manipulate data. We can chain them with the ``|>`` pipe:

  .. code-block:: coffeescript

     cards_with_stock = all_cards
     |> filter (.quantity > 0)

which is a shortcut to access an object's attribute or method. We can also write anonymous functions where ``it`` represents the method argument:

  .. code-block:: coffeescript

     cards_with_stock = all_cards
     |> filter ( -> it[quantity] > 0)

Huey: run asynchronous tasks
----------------------------

When a user action takes a long time and we want the server to respond
quickly, or when we want to run periodic tasks: we need a tasks queue,
and `Huey < https://huey.readthedocs.io/en/latest/ >`_ is one of them.

The most common solution is Celery, but it's a huge beast, with many
dependencies, and can be tricky to setup. Huey only depends on Redis
and on its python binding. It's also straightforward to use. Django-rq
could have been a solution, with the advantage of a Django dashboard.

We use Huey to **apply inventories**. See ``search.tasks.py``. To create
an async function we just add the ``db_task()`` decorator. Calling an
async function is just a regular function call. See
``search.models.api.py``.

Another nice usage will be sending periodic emails, or checking that
books prices didn't change.


Fabric: run management commands to the remote server
----------------------------------------------------

`Fabric <http://docs.fabfile.org/en/latest/>`_ helps to run remote
management commands to instances through ssh. See the ``fabfile.py``.

Deployment: Gunicorn and Whitenoise
-----------------------------------

Whitenoise makes it easier (than nginx and apache modules) to
self-contain a web app.

Gunicorn is full python (so has similar avantages).


Tox
---

`Tox <https://testrun.org/tox/latest/>`_ is a generic virtualenv
management and test command line tool we can use for:

- checking our package installs correctly with different Python

- running our tests in each of the environments, configuring our
   test tool of choice
- acting as a frontend to Continuous Integration servers, greatly
    reducing boilerplate and merging CI and shell-based testing.

Abelujo only runs on python2.7 at the moment. Tox helps us test that
our application installs and runs correctly in a fresh virtual
environment.


Sentry (Raven)
--------------

`Sentry <https://docs.sentry.io/clients/python/integrations/django/`_
is a tool that sends all uncaught exceptions to an online app. Logs on
steroids.

We have to create an account on give our sentry token to an Abelujo
instance. See the fabfile and its `save_variables` task. We put the
token in a `sentry.txt` file which Django settings read if the file
exists. Fabric is in charge of sending the token to a remote server on
installation.

Test with `python manage.py raven test` and see the new log in your
dashboard.

Technical choices
=================

Tox
---

`Tox <https://testrun.org/tox/latest/>`_ is a generic virtualenv
management and test command line tool we can use for:

- checking our package installs correctly with different Python
  versions and interpreters
- running our tests in each of the environments, configuring our
   test tool of choice
- acting as a frontend to Continuous Integration servers, greatly
    reducing boilerplate and merging CI and shell-based testing.

Abelujo only runs on python2.7 at the moment. Tox helps us test that
our application installs and runs correctly in a fresh virtual
environment.


Why AngularJS and not JQuery/Ember/<project xxx> ?
--------------------------------------------------

`AngularJS <https://angularjs.org/>`_ is a Model-View-Controller
framework to build dynamic user interfaces. It does double-data
binding at its core.

Angular isn't comparable with JQuery. See the basics: https://angularjs.org/#the-basics

Why not a simple library that does double data binding (like view.js)
? Because we will use all the power of Angular (we need js functions
as controllers and the like).

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

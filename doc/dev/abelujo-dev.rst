Abelujo development
===================

Install
-------

See the up to date instructions `on Gitlab <https://gitlab.com/vindarel/abelujo>`_.

See the Makefile for all the targets.

Run the development server
--------------------------

`make run` and open your browser on `localhost:8000`.


Run in production
-----------------

See ``make gunicorn``.

To restart the application, use ``make gunicorn-restart``.

See also ``fab start/stop/restart`` commands.


Debian specificity: name collision between node and nodejs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is installed with `make debian`::

    sudo apt-get install nodejs-legacy

Use the Postgresql database
---------------------------

We need to create a database with the following steps::

    sudo su - postgres
    createdb abelujo_db
    createuser abelujo_user -P # and enter a password.

Now call a postgresql prompt::

    psql
    GRANT ALL PRIVILEGES ON DATABASE abelujo_db TO abelujo_user;

Now we have a postgre database and a user ("postgres") to use it. We
just have to put it in our ``abelujo/settings.py``.

Create the db::

    ./manage.py syncdb

Note: if we have "authentication peer failed for user XXX", edit the
file ``/etc/postgresql/9.3/main/pg_hba.conf`` (which lists
permissions) and change::

    local all all peer

to::

    local all all trust


Populate the DB with our initial data
--------------------------------------

We may enjoy some initial data to start working with Abelujo: typical
book categories, default places and basket(s), etc. They will be
different depending on the user's needs and language.

We wrote a command to help define these in the most simple text file,
and create them in the database. The usage is::

    ./manage.py runscript add_objects --script-args=scripts/categories_fr.yaml

This tool isn't considered finished, you are fully in your right to ask for a simpler command.
For more info, ask and see the sources !


Write custom CSS
----------------

To customize the look of Abelujo, you can set your CSS rules in each
app ``<name of the app>/static/<name of the app>/style.css`` file,
i.e. in ``search/static/search/style.css``. This file will be loaded
automatically by Django, and collected when we run `collectstatic`
command.


Write JavaScript in Livescript
------------------------------

.. note::

   We used LiveScript but we're now switching to Vue.js with plain Javascript. https://vuejs.org

Our current Angularjs controllers are written in Livescript::

    * http://livescript.net

The LiveScript executable and repl is `lsc`.

Now to compile LiveScript files run `make gulp`.


You can recompile everything on every change with::

    gulp watch

.. note::

   If you have the same file with both a js and a ls extension, the
   javascript will take precedence (it is appended first in
   ``abelujo.js`` so it is read first by angularjs).


Testing strategy
----------------

We have different sorts of tests to write and run: unit tests, end to
end tests, tests of the user interface and integration tests.

Like with all python software, we write **unit tests**. They are aimed at
testing logical blocks of code, like a function on its own. We use the
`unittest` module and the Django facilities for the backend.

We must also unit test the javascript code (the logic lies in
angularjs controllers and directives).

Writing tests is mandatory to check that our code doesn't break with
time and refactorings. They are also necessary to reproduce and fix
bugs, and they are useful, when we write them, to better understand
and design the code we want to write. That's part of why a developper
should embrace the `Test Driven Development` (TDD) workflow: the goal
is to write tests before even writing the firt line of code.

Testing that a method does the expected logic doesn't guarantee that
it works with data from the real world. For example, let's consider
our web scrapers that pull data from online bookstores. We have to
write unit tests to check that they work as expected, but we also need
to test that they still work against the current website on the
internet. Indeed, remote websites can change, the format of the data
they accept or return can change and break our code. We then have to
run tests against the real world once in a while. We call those **end
to end tests**.

We also write a lot of javascript for **the user interface** in the
browser. Some pages do a lot of logic with javascript. The selling
page, for example: it asks for data to the server, it does some
calculation and it gives some data back to the server to be registered
in the database. We need to test all that too. This is doable with the
`testcafe <https://devexpress.github.io/testcafe/>`_ test framework.

Now we know how to test each part of our application. Great, but this
isn't enough. Nothing guarantees that those parts work happily
together ! We then need **integration tests**. They are fortunately
done partly with **testcafe** (because it launches a real web browser
with the current state of the application we can test the interaction
with the server).

But we also have to test that all the packages and software that we
rely on install correctly. We do it partially with `tox
<https://testrun.org/tox/>`_, which tests the python side, that our
`pip` dependencies install correctly in a fresh environment, and that
no one is missing ;) At is core it is made to test the installation
against multiple versions of python but we don't need that (yet).


Running Tests
-------------

To run python unit tests::

    make unit # or ./manage.py test search.tests.testfile.someClass.some_method

To run the javascript unit tests::

    TODO !

To run the javascript end-to-end tests, open 2
terminal windows:

- run our web app with the usual `make run` (or `./manage.py runserver`)
- run the tests: `make testcafe`.

.. note::

   Some tests rely on the testing data that we load with `make data`.

   You need at least nodejs v4 (so not Debian's default). See
   https://github.com/nodesource/distributions#installation-instructions
   and the Node Version Manager: https://github.com/creationix/nvm


Tests coverage
--------------

We simply use coverage (django\_coverage is buggy).

Run with::

    make cov
    # or:
    # coverage run --source='.' manage.py test search
    # coverage html  # and open: firefox htmlcov/index.html

How to contribute to Abelujo (git, gitlab, workflow)
----------------------------------------------------

To help develop Abelujo (welcome !) you need some basics in Python and
Git. Then you'll have to find your way in Django. You can help with
html, css and javascript too. And if you're experienced with
Docker, you'll have some work !

- Python crash course: http://learnpythonthehardway.org/book/
- Django documentation: https://docs.djangoproject.com/en/1.6/
- Python ecosystem: https://github.com/vinta/awesome-python

We use ``git`` as a source control system. You'll need to learn the
basics (essentially what ``git commit``, ``git pull``, ``git push``
and ``git branch`` do). To understand how creating branches help with
our workflow, see `the Github Flow
<https://guides.github.com/introduction/flow/index.html>`_ (just
replace Github by Gitlab).

- best Git ressource: http://www.git-scm.com/
- check out those git GUI too: http://www.git-scm.com/downloads/guis and `emacs' magit interface <https://magit.github.io/master/magit.html>`_.

Allright ! Take your time, I'll wait for you. The next step is easier,
you're going to **create an account on Gitlab.com**. Gitlab is a
web-based Git repository manager. It also has an issue tracking system
and a basic wiki. It's like Github, but there's an open-source
version of it. The sources of Abejulo are hosted on `Gitlab.com
<https://gitlab.com>`_ . So, go there and create an account. You don't
need one to grab the sources, but you need one to cooperate with us.

Indeed, the workflow is as follows:
- you have your copy of Abelujo, forked from the original (so that is
  nows where it comes from)
- you work on your repository.
- you regularly update your repository with the modifications of the
  original repository (you want to be up to date to avoid conflicts).
- when you're finished, you open a pull-request on Gitlab.
- we discuss it, it is eventually merged.

Once you have an account, you need to fork Abelujo's repository. With
your fork, you'll be able to (easily) suggest to us your new
developments (through pull-requests). So, go on `Abelujo's repository
<https://gitlab.com/vindarel/abelujo>`_ and click your "fork" button.

Now you can pull the sources of **yours** Abelujo copy::

    git clone git@gitlab.com:<your_user_name>/abelujo.git

Choose the ssh version of the link over the https one. With some
configuration of ssh on your side, you won't have to type your
username and password every time.

.. Note::

    If we recall well (ping us if needed), you need to add your ssh
    public key to your gitlab account (profile settings -> ssh
    keys). This key is located at "~/.ssh/id_rsa.pub". If it doesn't
    exist, create it with "ssh-keygen rsa". A passphrase isn't
    compulsory.

You're ready to work on your local copy of Abelujo. You can commit
changes and push them to your gitlab repository. Hey, we are also
working on it at the same time, so don't forget to *pull* the changes
once in a while, and to work in a branch distinct from master, this
will be easier.

And when you want to suggest changes to the official repository, you
press the button "Pull Request". We'll have a place to tchat about
your changes, and when a maintainer feels like it's ok, he or she will
merge your changes. We can also give you the right to do so.

Abelujo development
===================

Install
-------

Get the sources:::

    git clone https://gitlab.com/vindarel/abelujo.git

it creates the directory "abelujo".::

    cd abelujo

Install the dependencies for Debian (Ubuntu/Mint/etc):::

    make debian
    # a shortcut for
    # sudo apt-get install python-pip nodejs nodejs-legacy npm
	# sudo pip install virtualenvwrapper
	# sudo npm install gulp -g  # a JS build system.
    # Debian users have to install nodejs-legacy if the node command doesn't give you a javascript shell.


Create and activate a virtual environment (so than we can install python
libraries locally, not globally to your system). Do as you are used to,
or do the following:::

    # you need: sudo apt-get install python-pip
    sudo pip install virtualenvwrapper
    source venv_create.sh

now your shell prompt should show you are in the `abelujo`
virtualenv. To quit the virutal env, type `deactivate`. To enter it,
type `workon \<TAB\> abelujo`.

And now to install the dependencies and to create the database, run::

    make install

this will install Django and its requirements, set up the database,
install node and bower packages and build the static files.

We are done ! Now to try Abelujo, run the development server like this:::

    make run
    # or set the port with:
    # python manage.py runserver 9876

and open your browser to `http://127.0.0.1:8000 <http://127.0.0.1:8000>`_.

See the Makefile for all the targets.

Run the development server
--------------------------

See two lines above !


Use Apache's mod_wsgi for the development server
------------------------------------------------

Django's `manage.py runserver` development command is very handy but
doesn't represent a production server, in particular because it is
single-threaded. This isn't ideal. New problems may arise at the very
moment we deploy the application on a real server. To avoid that, we
must use the same server during development that the production one. A
popular choice is Apache's `mod_wsgi` and it is very easily usable on
development thanks to `mod_wsgi-express`.

See the full presentation by the author, it is really a good read: http://blog.dscpl.com.au/2015/05/using-modwsgi-express-as-development.html

In short, given `apache` and `apache-dev` are installed on our system,
we only one (or two) new python packages, `mod_wsgi`, which will
extend Django's `manage.py`.

The command to run a development server with Apache's `mod_wsgi`,
nearly like in production is now::

    python manage.py runmodwsgi --reload-on-changes

We then have new rules on our `Makefile` for shortcuts::

    make run-wsgi
    # you need manage.py collectstatic

This runs the server at the foreground. Multithreaded.

and::

    make run-wsgi-debug

This disables the auto-reloading of sources and the multithreading,
thus allowing to stop on a python debugger (`pdb`).

We then advise to use `mod_wsgi` the most possible.


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


Populate the DB with testing data
---------------------------------

Run:::

    make data

This will add cards, publishers and everything to the database so than
you can test it for real.

Populate the DB with real initial data
--------------------------------------

We may enjoy some initial data to start working with Abelujo: typical
book categories, default places and basket(s), etc. They will be
different depending on the user's needs and language.

We wrote a command to help define these in the most simple text file,
and create them in the database. The usage is::

    ./manage.py runscript add_objects --script-args=scripts/categories_fr.yaml

This tool isn't considered finished. For more info, see the sources !


Write custom CSS
----------------

To customize the look of Abelujo, you can set your CSS rules in each
app ``<name of the app>/static/<name of the app>/style.css`` file,
i.e. in ``search/static/search/style.css``. This file will be loaded
automatically by Django, and collected when we run `collectstatic`
command.


Write JavaScript in Livescript
------------------------------

Livescript is awesome::

    * http://livescript.net

You have livescript installed and configured if you ran `make install`
(or `make npm`), but nevertheless this is how you would do it
manually.

To install LiveScript and its main library:::

    npm install livescript prelude-ls -g

The LiveScript executable and repl is `lsc`.

Now to compile LiveScript files you could do it manually, but to
automate the process we use gulp so we need the ``gulp-livescript``
extension. It is installed with the `make install` (which calls `make
npm`) command.

We wrote a target in the gulpfile. Now you can run `gulp livescript`
to compile all the ``*.ls`` files found in ``static/js/app/`` and
concatenate them *with the other javascript sources* in
``static/js/build/abelujo.js``. This file is loaded in the html
template ``base.jade`` in a `script` tag::

      script(type='text/javascript', src="{% static 'js/build/abelujo.js' %}")

   which is necessary for the browser to load and run our javascript application.

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
`protractor <https://angular.github.io/protractor/>`_ test framework
from AngularJS.

Now we know how to test each part of our application. Great, but this
isn't enough. Nothing guarantees that those parts work happily
together ! We then need **integration tests**. They are fortunately
done partly with protractor (because it launches a real web browser
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

Python's end-to-end tests::

    make e2e

To run the javascript unit tests::

    TODO !

To run the javascript end-to-end tests (with Protractor), open 3
terminal windows:

- run our web app with the usual `make run` (or `./manage.py runserver`)
- start the webdriver: `make webdriver-start`
- at last, run the tests: `make protractor`. We also have a debugger
  mode with `make protractor-debug` (requires Chrome >= 39).

.. note::

   Some tests rely on the testing data that we load with `make data`.

We have also a Chrome extension to help us write Protractor tests:
https://github.com/andresdominguez/elementor (requires Chrome >= 39).
 Once we launch it::

     elementor # <url, i.e. http://localhost:8000/en/sell >

 we have a Chrome window open with a new extension installed (the red
 icon next to the url bar) where we can enter protractor selectors and
 see the result.

About Protractor:

- https://angular.github.io/protractor/#/getting-started
- api documentation: https://angular.github.io/protractor/#/api


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

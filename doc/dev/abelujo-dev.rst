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

Install and work on the Docker image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Why Docker ?

Before Docker came along, virtualenv was pretty much the tool of
choice for Python developers as it allows you to separate package
dependencies for different applications you're working on without
having to create separate virtual machines for each one. It worked
very well for me.

However, there are still some annoying things the developers will have
to deal with. Such things include having to install additional
applications and services required by the project such as PostgreSQL,
RabbitMQ, and Solr, for example. Also, some Python packages won't
install/compile properly without additional libraries installed on the
developer's machine. Pillow and lxml are just two that come to
mind. There is also the issue of predictability when you deploy to
production. You may be developing on a Mac but your production server
runs Ubuntu 12.04. Features that worked fine locally may have issues
when deployed to the servers.

Of course, virtual machines can solve these issues. But VMs are heavy,
take some time to start up, and if you like to separate services (say
a different VM for PostgreSQL), that could use up quite a bit of
system resources and if you use a laptop for development you will see
a pretty significant reduction in battery life.

With Docker, these issues go away. You can have all these services in
isolated Docker containers that are lightweight and start up very
quickly. You can use base images for different Linux distros,
preferably the same distro and version you use in production.

read more:

* tutorial: https://www.calazan.com/using-docker-and-docker-compose-for-local-django-development-replacing-virtualenv/
* Docker: https://docker.com/

Populate the DB with testing data
---------------------------------

Run:::

    make data

This will add cards, publishers and everything to the database so than
you can test it for real.


Try out RapydScript, the pythonic javascript
--------------------------------------------

First install RapydScript:::

    npm install rapydscript -g

Now to compile RapydScript files you could do it manually, but to do
it with gulp you need the ``gulp-rapyd`` extension. Install it with::

    npm install git://github.com/vindarel/gulp-rapyd

Now you can run `gulp rapyd`. This will compile all ``pyj`` files
found in ``static/js/app/`` and concatenate them in
``static/js/build/abelujo.js`` (check in the gulpfile.js) which is
loaded in the html template ``base.jade`` in a `script` tag::

    script(type='text/javascript', src="{% static 'js/build/abelujo.js' %}")

 which is necessary for the browser to load and run our javascript application.

You can recompile everything on every change with::

  gulp watch


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

And this isn't enough yet, because nothing guarantees that ``pip``
itself or ``node`` are installed correctly on the machine, which can be
a fresh or an old Debian, an Ubuntu, a web server, ... for that, we
started setting up `Docker` and a **continuous integration** server
on Gitlab.com. But that's an ongoing work.


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

About Protractor:

- https://angular.github.io/protractor/#/getting-started
- an extension: https://github.com/andresdominguez/elementor (requires
  Chrome >= 39)


Tests coverage
--------------

We simply use coverage (django\_coverage is buggy).

Run with::

    make cov
    # or:
    # coverage run --source='.' manage.py test search
    # coverage html  # and open: firefox htmlcov/index.html

Contribute to Abelujo
---------------------

To help develop Abelujo (welcome !) you need some basics in Python and
git. Then you'll have to find your way in Django. You can help with
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

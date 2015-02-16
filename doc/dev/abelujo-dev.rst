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


Populate the DB with testing data
---------------------------------

Run:::

    make data

This will add cards, publishers and everything to the database so than
you can test it for real.


Try out RapydScript
-------------------

First install RapydScript:::

    npm install rapydscript

Now to compile RapydScript files you could do it manually, but to do
it with gulp you need the ``gulp-rapyd`` extension. Install it with::

    npm install git://github.com/vindarel/gulp-rapyd

Now you can run ``gulp rapyd``. This will compile all ``pyj`` files
found in ``static/js/app/`` and concatenate them in
``static/js/build/rapyd.js``.

Remember to change the imported
scripts in ``base.jade`` (see the line importing `rapyd.js`).


Running Tests
-------------

Run::

    make unit # or ./manage.py test


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

We use ``git`` as a source control system. You'll need to learn the
basics (essentially what ``git commit``, ``git pull``, ``git push``
and ``git branch`` do). To understand how creating branches help with
our workflow, see `the Github Flow
<https://guides.github.com/introduction/flow/index.html>`_ (just
replace Github by Gitlab).

- best Git ressource: http://www.git-scm.com/
- check out those git GUI too: http://www.git-scm.com/downloads/guis and `emacs' magit interface <https://magit.github.io/master/magit.html>`_.

Abelujo development
===================

Install
-------

Get the sources:::

    git clone https://gitlab.com/vindarel/abelujo.git

it creates the directory "abelujo".::

    cd abelujo

Create and activate a virtual environment (so than we can install python
libraries locally, not globally to your system). Do as you are used to,
or do the following:::

    # you need: sudo apt-get install python-pip
    sudo pip install virtualenvwrapper
    source venv_create.sh

And now to install everything:::

    make install

this will install Django and its requirements, set up the database,
install node and bower packages and build the static files.

See the Makefile for all targets.


Debian error: name collision between node and nodejs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Then install:::

    sudo apt-get install nodejs-legacy


Populate the DB with testing data
---------------------------------

Run:::

    make data

This will add cards, publishers and everything to the database so than
you can test it for real.


Tests coverage
--------------

We simply use coverage (django\_coverage is buggy).

Run with::

    make cov
    # or:
    # coverage run --source='.' manage.py test search
    # coverage html  # and open: firefox htmlcov/index.html

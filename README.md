Abelujo - free software to manage small and independent book (and records) shops.
=================================================================================

This project is at its debut stage. However it is already possible to:

-   look up for **books**, either by keywords or by isbn/ean. *For now
    the search solely uses the french website chapitre.com, but it is
    possible to add other sources (we have one for Foyles coming, a
    londonian bookshop, and we are working on a way to make it very easy
    to write other scrapers).*
-   look up for **CDs** (via discogs.com)
-   choose how many exemplaries you add to your stock, edit the cards,
    search a book in your database
-   choose how many copies you put in what place
-   sell a book.

We base our work on the software specifications from the Ruche project
(to which we particpated):
<http://ruche.eu.org/wiki/Specifications_fonctionnelles>. We wrote there
what we understood about the work of a bookseller (like how to manage
different distributors, how to manage deposits, etc). You should read it
and tell us wether or not what we are doing will suit your needs (I'll
translate this document to english one day or another, but you should
tell me now if you're interested).

**Abelujo** means Beehive in Esperanto.

Feedback welcomed at ehvince at mailz dot org.

![looking for a registered card](doc/abelujo-collection.png)

Installation
============

Get the sources:

    git clone https://gitlab.com/vindarel/abelujo.git

it creates the directory "abelujo":

    cd abelujo

Create and activate a virtual environment (so than we can install python
libraries locally, not globally to your system). Do as you are used to,
or do the following:

    sudo pip install virtualenvwrapper  # you need: sudo apt-get install python-pip
    source venv_create.sh

now your shell prompt should indicate you are in the "abelujo"
virtualenv. To quit the virutal env, type "deactivate". To enter it,
type "workon \<TAB\> abelujo".

To install the dependencies, create and populate the database, run:

    ./install.sh

We are done ! Now to try Abelujo, run the development server like this:

    python manage.py runserver
    # or set the port with:
    # python manage.py runserver 9876

and open your browser to <http://127.0.0.1:8000>.

Enjoy ! Don't forget to give feedback at ehvince at mailz dot org !

How to update
-------------

For now, when you update the sources (git pull), you certainly will have
to run the installation process again. We may have updated some python
packages and the database is very likely to change too (and we didn't
set up some DB schema migration yet, so you'll have to delete it first,
meaning you'll loose your data).

Development
===========

Django project (1.6), in python (2.7).

We use:

-   **jade** templates, which compile to html: <http://jade-lang.com/>
    and pyjade for the Django integration
-   Bootstrap's CSS: <http://getbootstrap.com> and django-bootstrap3

We are currently working at expanding the database (adding locations,
distributors, …).

We get our data with some webscraping when needed (discogs provides an
api) which we do with those libraries:

-   requests (better than urllib)
-   selenium, if we need to interprate the javascript (sometimes needed
    to get the price or another important information),
-   beautifulsoup, to parse the html

You can have a look at the existing scrapers at search/datasources. Some
abstraction work remains to be done. And shall we use scrapy
<http://doc.scrapy.org/en/latest/intro/overview.html> ?

Load testing data
-----------------

For the moment, we have to delete the current database if the models
change, so we loose our data, but it is possible to load a small set
of testing data::

    ./manage.py loaddata dumpdata.json

this will load a handful of Cards, Authors, Publishers and
Baskets. There are already a default Place and Distributor.

Tests coverage
--------------

We simply use coverage (django\_coverage is buggy).

Run with:

    coverage run --source='.' manage.py test search
    coverage html  # and open: firefox htmlcov/index.html

Abelujo - free software to manage independent book (and records) shops.
=======================================================================

-------------------

**Please see https://gitlab.com/vindarel/abelujo/**

This GitHub mirror is out of sync.

--------------------

français: [Lisez-moi](https://gitlab.com/vindarel/abelujo/blob/master/README_fr.md "README en français")

This project is used daily by individuals, associations, tea and wine
shops, theaters, art centers and professional bookshops.

Abelujo allows to:

-   look up for **books**, either by keywords or by isbn/ean (which works with a **barcode scanner**). See the https://gitlab.com/vindarel/bookshops library. You can currently search for:

    * french books:
      * through [Dilicom](https://dilicom-prod.centprod.com) (the profesional provider)
      * or [librairiedeparis](http://www.librairie-de-paris.fr/)  ![](http://gitlab.com/vindarel/bookshops/badges/master/build.svg?job=french_scraper)
    * spanish books (through [casadellibro.com](http://www.casadellibro.com)) ![](http://gitlab.com/vindarel/bookshops/badges/master/build.svg?job=spanish_scraper)
    * german books(through [buchlentner.de](http://www.buchlentner.de)) ![](http://gitlab.com/vindarel/bookshops/badges/master/build.svg?job=german_scraper)
    * *you want another one ? The sooner you tell us, the quicker you'll have it ;)*
-   look up for **CDs** (via [discogs.com](http://www.discogs.com/))
-   do **inventories** of your stock,
-   manage lists of books, export them to **csv** and **pdf** (with **barcodes**),
-   send an email to distributors to **order** books,
-   manage deposits and distributors, see **the balance of your deposits**,
-   sell books, see the history,

It is translated to English, French and Spanish.

We base our work on the software specifications from the Ruche project
(to which we particpated):
<http://ruche.eu.org/wiki/Specifications_fonctionnelles>. We wrote there
what we understood about the work of a bookseller (like how to manage
different distributors, how to manage deposits, etc). You should read it
and tell us wether or not what we are doing will suit your needs (I'll
translate this document to english one day or another, but you should
tell me now if you're interested).

**Abelujo** means Beehive in Esperanto.

Enjoy!

<a href="https://liberapay.com/vindarel/donate"><img alt="Donate using Liberapay" src="https://liberapay.com/assets/widgets/donate.svg"></a>

![looking for a registered card](doc/abelujo-search-isbn.png)

Installation
============

**note:** if you are getting started and are feeling adventurous, use the `django20py3` branch: it uses Python 3.6 and one of the latest Django version (2.2). For stability, stay with master.

Instructions for Debian 9.

[![build status](https://gitlab.com/vindarel/abelujo/badges/master/build.svg)](https://gitlab.com/vindarel/abelujo/commits/master)

Either do the quick way:

    apt install curl -y && curl -sS https://gitlab.com/vindarel/abelujo/raw/master/install.sh | bash -

this will clone the repo in the current directory and install all its dependencies.

or read below for the detailed instructions.

See after to install without sudo.

Get the sources:

    git clone --recursive https://gitlab.com/vindarel/abelujo.git

it creates the directory "abelujo":

    cd abelujo

Ensure you have Python 2.7.

Install the required dependencies for Debian (Ubuntu/LinuxMint/etc):

    make debian
    # a shortcut for
    # sudo apt-get install python-pip
	# sudo pip install virtualenvwrapper

Create and activate a virtual environment (so than we can install python
libraries locally, not globally to your system). Do as you are used to,
or do the following:

    source venv_create.sh # [venvname] (optional argument)
    workon abelujo

now your shell prompt should show you are in the `abelujo`
virtualenv. To quit the virutal env, type `deactivate`. To enter it,
type `workon \<TAB\> abelujo`.


To install the dependencies, create and populate the database, run:

    make install

We are done ! Now to try Abelujo, run the development server like this:

    make run
    # or set the port with:
    # python manage.py runserver 9876

and open your browser to <http://127.0.0.1:8000> (admin/admin).

You might need to create a superuser: see [the dev documentation](http://dev.abelujo.cc/use-manage.html).


Install without sudo
--------------------

    make debian-nosudo
    make install-nosudo

please read the Makefile in this particular case.


How to update
-------------

To update, you need to: pull the sources (`git pull --rebase`),
install new packages (system and python-wide), run the database
migrations, build the static assets and, in production, collect the
static files.

In the virtual env, run:

    make update
    # git pull --rebase
    # git submodule update --remote
    # install pip, migrate, compile transalation files.

Actions required for updates
----------------------------

- for version **0.8** (january, 24th 2020): update pip, run `make
update`, and start the new task queue with `make taskqueue`. You don't
need Redis anymore.

Development
===========

Django project, in python (2.7) and JavaScript (AngularJS).

We use:

- [LiveScript](http://livescript.net)
- [jade templates](http://jade-lang.com/), which compile to html,
    and pyjade for the Django integration
- [Bootstrap's CSS](http://getbootstrap.com) with django-bootstrap3
- the [Django-q](https://django-q.readthedocs.org/) asynchronous task queue.

See the developer documentation: http://dev.abelujo.cc/.

This is [our database graph](http://dev.abelujo.cc/graph-db.png)
(`make graphdb`).

### Dev installation ###

As a complement to the installion procedure above, you also need to
install development dependencies that are listed in another
requirements file::

    make pip-dev

and npm packages

    make npm
    # this installs node dependencies

Then, to build the JS and CSS:

    make gulp

and commit the result.

Also install npm packages to run end to end tests:

    make npm-dev  # packages listed in devDependencies of packages.json


### Vagrant and Ansible role

You can install and try everything in a Vagrant virtual machine, thanks to a nice contribution: https://gitlab.com/anarchistcat/abelujo-ansible

## Configure services

### Task queue (mandatory)

We need a task queue for long operations (notably applying an inventory to the stock). We use Django-q in pure-Django mode (no more Redis).

Start it with

    make task-queue &
    # aka honcho start &

### Sentry (optional)

Put your
[Sentry](https://docs.sentry.io/clients/python/integrations/django/)
private token in a `sentry.txt` file. The settings will see and read
it.

To get Fabric send it to the remote instance on install (`fab install`
calls `fab save_variables`), add the token into your `clients.yaml`
under `sentry_token` (see the fabfile).

Test with `python manage.py raven test` and see the new message in your dashboard.


### Electre API (optional)

We support fetching data on Electre's API. We can search by ISBN or with a free text search.

The `pyelectre` module is developed separately, you will to get in touch with us.


Run unit tests
--------------

    make unit

Code coverage:

    make cov  # and open your browser at htmlcov/index.html

Testing the installation script in Docker (experimental)
--------------------------------------------------------

Given you have Docker already installed, run the installation script
in a fresh Ubuntu 16.04 with:

    chmod +x dockentry.sh
    docker run  -v "$(pwd)/docker":/home/docker/ -ti ubuntu:16.04 /home/docker/dockentry.sh

The script given as argument creates a user with sudo rights and then
calls the installation script.

You can also simply step into the image and run scripts manually from
there.

See a bit more in doc/dev/ci.rst.


Load data
---------

See the scripts in `scripts/` to load data (specially shelves
names), in different languages.

Troubleshooting
---------------

If you get:

    OperationalError: no such column: search_card.card_type_id

it is probably because you pulled the sources and didn't update your
DB. Use database migrations (`make migrate`).

Uninstall
---------

To uninstall Javascript and Python libraries, see `make uninstall[-js, -pip]`.

The most worth it is to uninstall JS libs from `node_modules`, that
frees a couple MB up.


Documentation
-------------

We have developer documentation: http://dev.abelujo.cc/

Licence
-------

AGPL-3.0

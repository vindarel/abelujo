Installation - locally and on a server
======================================


See the up to date instructions `on Gitlab <https://gitlab.com/vindarel/abelujo>`_.

See the Makefile for all the targets.

Run the development server (local)
----------------------------------

`make run` and open your browser on `localhost:8000`.

You must create a user (see management commands to create and delete
superusers in the next section).

This command is only to be run on a local machine. If you run it on a
server, you won't be able to access Abelujo from the internet. But you could do::

  ./manage.py runserver PORT:IP


Run in production (server)
--------------------------

Put your ip address in the file `IP.txt` (root of the project) and the
port in `PORT.txt`::

    echo "my.ip" > IP.txt
    echo "8888" > PORT.txt

and run the server with ``make gunicorn``.

To restart the application, use ``make gunicorn-restart``.

See also the ``fab start/stop/restart`` commands.


Some tasks need to run asynchronously (applying an inventory,…). Start
 the asyncronous task runner with::

    make taskqueue


deployment and website management
---------------------------------

We use gunicorn and whitenoise to serve static files.

- http://docs.gunicorn.org/en/latest/
- https://github.com/evansd/whitenoise

Fabric helps to run remote management commands.

- http://docs.fabfile.org/en/latest/

At the project root, type ``fab <TAB>`` and see the suggested actions.

Available commands so far:

- create a new client
- install a new Abelujo instance
- update a specific project (fully, or a light update without calling
  apt nor npm)
- start, stop, restart a website
- check the status of one or all projects
- check how the projects are up to date with the main branch (how many
  commits behind)
- upload a file to the server
- run any make command in a specific project
- ...

Setup Sentry (issues monitoring)
--------------------------------

Sentry helps immensely in being notified of runtime errors.

See the `save_variables` fabric task and how the settings read the
Sentry token in a `sentry.txt` file if present. Fabric is in charge of
sending the token to a remote instance on its installation.

Test with `python manage.py raven test`.



Debian specificity: name collision between node and nodejs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is installed with `make debian`::

    sudo apt-get install nodejs-legacy

Use the Postgresql database
---------------------------

(but you can stay with SQLite)

Abelujo uses by default an SQLite database, you don't *have* to
configure a Postgresql one.

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

This command is required::

  make db

Furthermore, we wrote a command to help define data in the most simple text file,
and create them in the database. The usage is::

    ./manage.py runscript add_objects --script-args=scripts/categories_fr.yaml

(this command is not required)

This tool isn't considered finished, you are fully in your right to ask for a simpler command.
For more info, ask and see the sources !


In the next topic, see the available management commands.


Post-installation: set personal settings
----------------------------------------

Set the default datasource: if you want to search on the Swiss source
by default, use a shell variable::

  export DEFAULT_DATASOURCE='lelivre'

and then start Abelujo.

Set other variables in a configuration file.

Create a file ``config.py`` at the project root.

Make it start with the following line::

  # -*- coding: utf-8 -*-

Abelujo will read the following variables at startup:

* PAYMENT_CHOICES, for the sell page. For example::

  PAYMENT_CHOICES = [
    (1, "ESPÈCES"),
    (7, "MAESTRO"),
    (10, "MASTERCARD"),
    (11, "VISA"),
    (12, "interne"),
    (13, "en attente"),
    (6, "autre"),
  ]

(see ``models/common.py`` for the default ones)

Each entry must have a distinct id.

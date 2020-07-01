Administration, custom management commands
==========================================

In addition to using the fabfile commands, an Abelujo administrator
may need to work manually on websites. Here some tips and pointers.

.. note::

   all commands have to be run at the project root and with the python
   virtualenv activated (``workon abelujo`` or ``source
   bin/activate``) unless stated otherwise.

Add and delete users
--------------------

There is no graphical way to add users yet, but a Django management command::

        ./manage.py createsuperuser

this will ask for a user name and an email adress.


Delete a superuser::

        ./manage.py deletesuperuser <username>


And list all::

  ./manage.py listsuperusers


Change a user password
----------------------

A user connected to his session can change his password. Go to the
Database interface and see a drop-down button at the top right corner
with an option to change the password.

An administrator can also do it from the command line::

    ./manage.py changepassword username


Re-initialize quantities to zero
--------------------------------

Use our custom management command `reset_quantities`::

        ./manage.py reset_quantities


Managing inventories
--------------------

To **apply** an inventory from the command line, use ``apply_inventories --ids [id id,id,…]``.

Its argument is either one id or a coma-separated list of ids (no spaces in between).

To **appy all open inventories**, use ``--all``.


To **archive** a bunch of inventories in a row (archive and close), use ``archive_inventories --all --ids``.

These command ask for confirmation before applying the changes.


Import a csv file of ISBNs and quantities
-----------------------------------------

The CSV file has two columns: the ISBN and the quantity.

This command will search for the bibliographic information of this
ISBN and save it to the database with the given quantity.

You can export your Excel or LibreOffice calc sheet into csv, preferably
with a ``;`` as separator.

Use the ``import_isbns`` command::

  ./manage.py import_isbns -i myfile.csv

Options:

- ``-l`` to choose the language of the bibliographic search (a french
  source by default)
- ``-s <id>`` to choose a shelf.

The script will search each ISBN on the datasource, create a Card
object, and save the given quantity into the default Place. Consequently, before running the script, you must choose the appropriate default place.

If an ISBN is not found, the script carries on and prints all the ones not found at the end.

**update january, 2020**: the script was not indempotent but is now. You can run it twice in a row, it will not add up the quantities, only set them.

If you need more features, get in touch.


Import the list of distributors known by Dilicom
------------------------------------------------

Dilicom provides a list of distributors in CSV format. It defines more
than 5.000 distributors in 52 countries.

Each line contains:

* its GLN
* its name, city, postal code, country
* the number of titles distributed by Dilicom
* wether it is communicated within the FEL (yes or no)

To import all the data, run::


    ./manage.py import_dists

This will take a couple of minutes.

You probably don't need this if you don't use the FEL.


Update all the books with Dilicom
---------------------------------

You need this if you used Abelujo before subscribing to Dilicom.

You must have Dilicom credentials.

You can update all the books data:

- distributor
- publisher
- thickness, height, width, weight
- parution date
- theme
- etc

Run::

  DILICOM_USER=foo DILICOM_PASSWORD=bar ./manage.py update_all_with_dilicom


Delete unused publishers
------------------------

This can happen specially after the full update from Dilicom. Run::

  ./manage.py delete_unused_publishers

There is a confirmation prompt.


Other management commands
-------------------------

Transforming a shelf to a place::

  ./manage.py shelf2place --shelf=<id> [--can_sell true/false]

Use case: we did the inventory, and it turned out that "mezzanine"
should be the stocking place, not a shelf (so we can know what's in
the reserve).

Transform the shelf into a place of the same name with ALL the cards
from the default place. We don't create a movement object.

Consequently the moved cards won't have an associated shelf
anymore.  The shelf object will be deleted, and the
inventories made against it too.  You might want to save or
export your DB beforehand.

Administration, custom management commands
==================================================

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

Use our custom management command `my_reset_quantities` (all our
custom commands start with `my_` for better exploration).::

        ./manage.py my_reset_quantities

If you wish to be more precise (set to n copies instead of zero, reset
for only a place), this needs more work. See the method
`Card.quantities_to_zero` and the same on `Place`.

Import a csv file of ISBNs and quantities
-----------------------------------------

First export your Excel or LibreOffice calc sheet into csv, preferably
with ``;`` as separator, then use the ``import_isbns`` command::

  ./manage.py import_isbns -i myfile.csv

Options:

- ``-l`` to choose the language of the bibliographic search (a french
  source by default)

The script will search each ISBN on the datasource, create a Card
object, and add the given quantity into the default Place. Consequently, before running the script, you must choose the appropriate default place.

The script will fail early if any error were to occure.

**warning**: presently the script is not indempotent, meaning if you run it twice, it will add twice the quantities.

If you need more features, get in touch.

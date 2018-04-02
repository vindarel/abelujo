Abelujo administration, custom management commands
==================================================

In addition to using the fabfile commands, an Abelujo administrator
may need to work manually on websites. Here some tips and pointers.

.. note::

   all commands have to be run at the project root and with the python
   virtualenv activated (``workon abelujo`` or ``source
   bin/activate``) unless stated otherwise.

Add users
---------

There is no graphical way to add users yet, but a Django management command::

        ./manage.py createsuperuser

this will ask for a user name and an email adress.


Change a user password
----------------------

A user connected to his session can change his password. Go to the
Database interface and see a drop-down button at the top right corner
with an option to change the password.

An administrator can also do it from the Python prompt.

Start it::

  make shell

Look at all users::

  User.objects.all()

Find your user by id::

  user = User.objects.filter(id=1).first()

Change the password::

  user.set_password("new password")

Save in DB::

  user.save()

quit with ``C-d``.



Re-initialize quantities to zero
--------------------------------

Use our custom management command `my_reset_quantities` (all our
custom commands start with `my_` for better exploration).::

        ./manage.py my_reset_quantities

If you wish to be more precise (set to n copies instead of zero, reset
for only a place), this needs more work. See the method
`Card.quantities_to_zero` and the same on `Place`.
Deployment and website management
=================================

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
  apt, npm nor bower)
- start, stop, restart a website
- check the status of one or all projects
- check how the projects are up to date with the main branch (how many
  commits behind)
- upload a file to the server
- run any make command in a specific project
- check a bower package version
- ...

Abelujo administration, custom management commands
==================================================

In addition to using the fabfile commands, an Abelujo administrator
may need to work manually on websites. Here some tips and pointers.


Re-initialize quantities to zero
--------------------------------

Use our custom management command `my_reset_quantities` (all our
custom commands start with `my_` for better exploration).::

        ./manage.py my_reset_quantities

If you wish to be more precise (set to n copies instead of zero, reset
for only a place), this needs more work. See the method
`Card.quantities_to_zero` and the same on `Place`.

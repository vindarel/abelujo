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

Setup Sentry (Raven)
====================

See the `save_variables` fabric task and how the settings read the
Sentry token in a `sentry.txt` file if present. Fabric is in charge of
sending the token to a remote instance on its installation.

Test with `python manage.py raven test`.



#!/bin/bash

pip install -r abelujo/requirements.txt     # install python libraries locally

python manage.py syncdb --noinput           # populate the db for django
python manage.py loaddata dbfixture.json    # set admin user (admin/admin)
# to run it:
# python manage.py runserver 8000
# and open your browser at localhost:8000

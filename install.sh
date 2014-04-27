#!/bin/bash

pip install -r abelujo/requirements.txt     # install python libraries locally

python manage.py syncdb --noinput           # populate the db for django
python manage.py loaddata dbfixture.json    # set admin user (admin/admin)
python manage.py test search && python manage.py runserver # and open your browser to localhost:8000

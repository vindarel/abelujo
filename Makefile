#!/usr/bin/env make

# Makefile: because we need more elaborate commands than manage.py

# The target names are not a file produced by the commands of that target. Always out of date.
.PHONY: clean unit test data cov odsimport doc install_script npm gulp tox migrations shell

clone:
	git clone --recursive https://gitlab.com/vindarel/abelujo.git

# System dependencies to install as root on Debian (Ubuntu/LinuxMint):
debian-nosudo:
	@grep -v "^#" abelujo/apt-requirements.txt | xargs apt-get install -y
	@grep -v "^#" abelujo/apt-requirements-dev.txt | xargs apt-get install -y
	pip install --upgrade pip
	pip install virtualenvwrapper

debian:
	@grep -v "^#" abelujo/apt-requirements.txt | xargs sudo apt-get install -y
	@grep -v "^#" abelujo/apt-requirements-dev.txt | xargs sudo apt-get install -y
	@sudo pip install --upgrade pip
	@sudo pip install virtualenvwrapper

# Rebase main repo and submodules
rebase:
	git pull --rebase
	git submodule update --remote

# Install in current directory
pip: pip-submodule
	@pip install -r abelujo/requirements.txt     # install python libraries locally
	make pip-system

pip-nosudo: pip-submodule pip-system-nosudo
	pip install -r abelujo/requirements.txt

pip-system:
	sudo pip install -r abelujo/requirements-system.txt # venvs have access to them with --system-site-packages
pip-system-nosudo:
	pip install -r abelujo/requirements-system.txt

pip-dev:
	@pip install -r abelujo/requirements-dev.txt # other python libs, for development

pip-submodule:
	cd search/datasources && pip install -r requirements.txt

pip-submodule-dev:
	cd search/datasources && pip install -r requirements-dev.txt

db:
	@python manage.py syncdb --noinput           # populate the db for django
	@python manage.py loaddata dbfixture.json    # set admin user (admin/admin)

dbback:
	# back up the db, append a timestamp
	bash -c "cp db.db{,.`date +%Y%m%d-%H%M%S`}"

install-nodejs:
	@echo "Installing nodejs from a new deb source..."
	curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
	sudo apt-get install -y nodejs
	sudo make install-yarn

install-yarn:
	@echo "Installing the yarn package manager..."
	# curl -o- -L https://yarnpkg.com/install.sh | bash  # fails in gitlab CI, seems lacking in path "yarn installed but doesn't seem to be working".
	# export PATH="$HOME/.yarn/bin:$PATH"
	curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
	echo "deb http://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
	apt-get update && apt-get install -y yarn

# Install everything: Django requirements, the DB, node packages, and
# build the app.
install:  debian pip pip-submodule db npm-system npm gulp collectstatic translation-compile

# xxx: there must be a better way (to do the same task with and without sudo)
install-nosudo:  debian-nosudo pip-nosudo db npm-system-nosudo npm gulp collectstatic translation-compile

install-dev:  debian pip pip-dev pip-submodule pip-submodule-dev db npm npm-dev gulp translation-compile

# Install npm packages
npm-system:
	@echo "Installing gulp globally... (needs root)"
	@sudo npm install -g gulp
npm-system-nosudo:
	@echo "Installing gulp globally... (needs root)"
	yarn global add gulp

npm:
	@echo "Installing Node packages..."
	yarn install --production # don't install devDependencies
	# Saving dev ip for gunicorn
	echo "localhost" > IP.txt
	@echo "Note for Debian users: if you get an error because of name clashes (node, nodejs), then install nodejs-legacy:"
	@echo "sudo apt-get install nodejs-legacy"

npm-dev:
	yarn install # not in production, install also devDependencies

set-prod:
	touch PROD.txt

update:
	make set-prod
	make rebase
	# Get code, install new packages, run DB migrations, compile JS and translation files.
	@grep -v "^#" abelujo/apt-requirements.txt | xargs sudo apt-get install -y
	make pip
	make pip-submodule
	make npm  # actually now yarn. Wishing to fix long and undpredictable builds.
	python manage.py migrate
	gulp
	make collectstatic
	make translation-compile 	# gunicorn needs a restart
	# echo "it's good to do an apt-get update once in a while"  # prevents unreachable sources, sometimes.
	@echo "For development, don't forget make pip-dev"

update-dev: update pip-dev pip-submodule-dev

# Create migrations and commit them.
migrations:
	python manage.py makemigrations
	git add search/migrations/*.py

migrate:
	python manage.py migrate --noinput

collectstatic:
	python manage.py collectstatic --noinput

# Run the tests of the UI in a browser.
NODEBIN=./node_modules/.bin/
PROTRACTOR_CMD=$(NODEBIN)protractor
PROTRACTOR_CONF=search/tests/integration-tests/conf.js
# Start the webdriver before the protractor tests.
webdriver-start:
	$(NODEBIN)webdriver-manager start

livescript: search/tests/integration-tests/*.ls
	# compile livescript files
	cd search/tests/integration-tests/ && lsc -c *.ls

protractor: livescript
	@echo "you need: make run and make webdriver-start"
	$(PROTRACTOR_CMD) $(PROTRACTOR_CONF)

protractor-debug:
	$(PROTRACTOR_CMD)  --elementExplorer $(PROTRACTOR_CONF)
	@echo "Chrome version must be >= 39.0"

end2end:
	# it was buggy on Firefox (waiting for async/await ?).
	testcafe chromium search/tests/integration-tests/testcafetest.js

# Build static files
gulp:
	gulp

# Run the dev server
run:
	# python manage.py runserver 8000
	python manage.py runserver_plus 8000

run-wsgi:
	# Run a development server using Apache and mod_wsgi, like in production.
	# required: run collectstatic.
	# see also --log-to-terminal, --enable-coverage, --profiler-
	python manage.py runmodwsgi --reload-on-changes

run-wsgi-prod:
	# TODO: run as daemon.
	# https://pypi.python.org/pypi/mod_wsgi#running-mod-wsgi-express-as-root
	python manage.py runmodwsgi

run-wsgi-debug:
	# Allows: single thread, pdb, debug on exception
	# Disables: auto code reloading, multithreading.
	python manage.py runmodwsgi --debug-mode --enable-debugger

# Get our IP adress, only ipv4 form, trim whitespaces. Works for localhost.
# MAINIP := $(shell hostname --ip-address | cut -d " " -f 2 | tr -d '[[:space:]]')
# put the IP in IP.txt: ok for dev and prod
run-gunicorn:
	# and static files are served by whitenoise.
	# option --reload to reload on code changes. use --daemon or C-z and bg
	gunicorn --env DJANGO_SETTINGS_MODULE=abelujo.settings abelujo.wsgi --bind=$(shell cat IP.txt):$(shell cat PORT.txt) --reload --pid=PID.txt
	@echo "server running on $(shell cat IP.txt):$(shell cat PORT.txt)"

gunicorn-daemon:
	gunicorn --env DJANGO_SETTINGS_MODULE=abelujo.settings abelujo.wsgi --bind=$(shell cat IP.txt):$(shell cat PORT.txt) --reload --pid=PID.txt --daemon
	@echo "server running on $(shell cat IP.txt):$(shell cat PORT.txt)"


kill-gunicorn:
	kill -9 $(shell cat PID.txt)

gunicorn: run-gunicorn

shell:
	python manage.py shell_plus

taskqueue:
	python manage.py run_huey

# run only unit tests.
unit:
	# TODO: use django-nose or move datasources.
	# With this pattern we don't run the tests from "datasources".
	./manage.py test search.tests --pattern="tests_*.py"

# Run test of an independent module.
ods:
	cd search/datasources/bookshops/odslookup/tests/ && nosetests --nologcapture

# Test the scrapers but not the ods module.
testscrapers:
	@cd search/datasources/frFR/ && nosetests
	@cd search/datasources/deDE/buchwagner/ && nosetests

# Run all tests possible.
test: unit ods testscrapers

testcafe:
	# Firefox has pbs with the new syntax (async/await).
	cd search/tests/integration-tests/ && testcafe chromium test*.js

# Build test virtual environments, test against multiple python versions.
# see tox.ini
tox:
	@tox

# Install the app in a fresh environment
ci:
	source ci-testing.sh

# Code coverage analysis:
cov:
	coverage run --source='search/' --omit='*/admin.py,*/*LiveTest*' manage.py test search
	# XXX: discogs unit tests are missing.
	coverage html
	@echo -n "Current status:"
	@coverage report | tail -n 1 | grep -o "..%"
	@echo "You can now open the page htmlcov/index.html"

# Import from an ods file (LibreOffice Calc)
# usage: make odsimport srcfile=myfile.ods
srcfile = ""
odsimport:
	python manage.py runscript -v2 odsimport --script-args=$(srcfile)

graphdb: doc/dev/graph-db.png
	# DB graph with graphviz (apt-get install graphviz), and django_extensions
	./manage.py graph_models  search | dot -Tpng -o doc/dev/graph-db.png

doc: graphdb
	# the chmod is for the host server to serve the files.
	@cd doc/dev/ && make html && cp *png _build/html/ && chmod 777 -R _build/html/

publish: doc
	# publish on dev.abelujo.cc
	@rsync -avzr doc/dev/_build/html/ $(ABELUJO_USER)@$(ABELUJO_SERVER):$(ABELUJO_HTDOCS)

html: doc

# I18n, translation.
# doc: https://docs.djangoproject.com/en/1.7/topics/i18n/translation/#localization-how-to-create-language-files
translation-files:
	# py, html, jade files and all locales:
	python manage.py makemessages  --ignore="collectedstatic/*" --ignore="node_modules/*" -a -e py,html,jade
	# Same for js files (djangojs flag) (compile .ls files before):
	# (we may want to translate js in admin/)
	# check the --ignore flags...
	django-admin.py makemessages -d djangojs --ignore="doc/dev/_build/*" --ignore="static/js/build/vendor.js" --ignore="static/lib/*" --ignore="./static/bower_components/" --ignore="node_modules/*" --ignore="bootstrap/*" --ignore="admin/js/*" --ignore="collectedstatic/*" -a

translation-compile:
	django-admin.py compilemessages 	# gunicorn needs a restart

flake8:
	flake8 --config=setup.cfg abelujo *.py

pylint:
	pylint abelujo search

clean:
	find . -name "*.pyc" -exec rm {} +
	rm -rf htmlcov
	rm -rf .coverage

clean-caches:
	# that can be needed when moving scraper code.
	find . -name "cache.sqlite" -exec rm {} +

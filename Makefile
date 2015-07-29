#!/usr/bin/env make

# Makefile: because we need more elaborate commands than manage.py

# The target names are not a file produced by the commands of that target. Always out of date.
.PHONY: clean e2e unit test data cov odsimport doc install_script npm gulp tox

# System dependencies to install as root on Debian (Ubuntu/LinuxMint):
debian:
	@grep -v "^#" abelujo/apt-requirements.txt | xargs sudo apt-get install -y
	@grep -v "^#" abelujo/apt-requirements-dev.txt | xargs sudo apt-get install -y
	@sudo pip install --upgrade pip
	@sudo pip install virtualenvwrapper

# Install in current directory
deps:
	@pip install -r abelujo/requirements.txt     # install python libraries locally

db:
	@python manage.py syncdb --noinput           # populate the db for django
	@python manage.py loaddata dbfixture.json    # set admin user (admin/admin)

# Install everything: Django requirements, the DB, node packages, and
# build the app.
install:  deps db npm gulp

# Install npm and bower packages
npm:
	@echo "Installing Node and bower packages..."
	npm install
	@echo "Installing gulp and rapydscript globally... (needs root)"
	# Don't install protractor globally, we'll have permission pb with the webdriver.
	@sudo npm install -g gulp rapydscript elementor
	# Install or update Selenium etc (XXX: development only).
	./node_modules/protractor/bin/webdriver-manager update
	@echo "Note for Debian users: if you get an error because of name clashes (node, nodejs), then install nodejs-legacy:"
	@echo "sudo apt-get install nodejs-legacy"

# Run the tests of the UI in a browser.
NODEBIN=./node_modules/.bin/
PROTRACTOR_CMD=$(NODEBIN)protractor
PROTRACTOR_CONF=search/tests/integration-tests/conf.js
# Start the webdriver before the protractor tests.
webdriver-start:
	$(NODEBIN)webdriver-manager start

protractor:
	$(PROTRACTOR_CMD) $(PROTRACTOR_CONF)

protractor-debug:
	$(PROTRACTOR_CMD)  --elementExplorer $(PROTRACTOR_CONF)
	@echo "Chrome version must be >= 39.0"

# Build static files
gulp:
	gulp

# Run the dev server
run:
	python manage.py runserver 8000

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

# Run end to end tests only.
e2e:
	cd search/ && ./e2etests.sh

# run only unit tests.
unit:
	#TODO: use django-nose or move datasources.
	# With this pattern we don't run the tests from "datasources".
	./manage.py test search --pattern="tests*.py"

# Run test of an independent module.
ods:
	cd search/datasources/odslookup/tests/ && nosetests --nologcapture

# Test the scrapers but not the ods module.
testscrapers:
	@cd search/datasources/frFR/ && nosetests
	@cd search/datasources/deDE/buchwagner/ && nosetests

# Run all tests possible.
test: unit e2e ods testscrapers

# Build test virtual environments, test against multiple python versions.
# see tox.ini
tox:
	@tox

# Install the app in a fresh environment
ci:
	source ci-testing.sh

# Load sample data, for testing purposes.
data:
	./manage.py loaddata dumpdata-big

# Code coverage analysis:
cov:
	coverage run --source='search/' --omit='*/admin.py,*/*LiveTest*' manage.py test search
	#XXX: discogs unit tests are missing.
	coverage html
	@echo -n "Current status:"
	@coverage report | tail -n 1 | grep -o "..%"
	@echo "You can now open the page htmlcov/index.html"

# Import from an ods file (LibreOffice Calc)
# usage: make odsimport odsfile=myfile.ods
src = ""
odsimport:
	python manage.py runscript odsimport --script-args $(src)

doc:
	@cd doc/dev/ && make html

publish:
	# publish on dev.abelujo.cc
	# @rsync -avzr doc/dev/_build/html/ $(ABELUJO_USER)@$(ABELUJO_SERVER)w4a152947@ssh.web4all.fr:/datas/vol3/w4a152947/var/www/dev.abelujo.cc/htdocs/
	@rsync -avzr doc/dev/_build/html/ $(ABELUJO_USER)@$(ABELUJO_SERVER):$(ABELUJO_HTDOCS)

html: doc

# I18n, translation.
# doc: https://docs.djangoproject.com/en/1.7/topics/i18n/translation/#localization-how-to-create-language-files
translation-files:
	# py, html, jade files and all locales:
	python manage.py makemessages -a -e py,html,jade
	# Same for js files:
	# (we may want to translate js in admin/)
	django-admin.py makemessages -d djangojs --ignore="static/bower_components/*" --ignore="static/lib/*" --ignore="node_modules/*" --ignore="bootstrap/*" --ignore="admin/js/*" -a

translation-compile:
	django-admin.py compilemessages

clean:
	find . -name "*.pyc" -exec rm {} +
	rm -rf htmlcov
	rm -rf .coverage

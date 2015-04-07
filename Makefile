#!/usr/bin/env make

# Makefile: because we need more elaborate commands than manage.py

# The target names are not a file produced by the commands of that target. Always out of date.
.PHONY: clean e2e unit test data cov odsimport doc install_script npm gulp tox

# System dependencies to install as root on Debian (Ubuntu/LinuxMint):
debian:
	@sudo apt-get install -y python-pip nodejs nodejs-legacy npm
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
	@sudo npm install gulp -g
	@echo "Note for Debian users: if you get an error because of name clashes (node, nodejs), then install nodejs-legacy:"
	@echo "sudo apt-get install nodejs-legacy"

# Build static files
gulp:
	gulp

# Run the dev server
run:
	python manage.py runserver 8000  # should check the port

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

html: doc

clean:
	find . -name "*.pyc" -exec rm {} +
	rm -rf htmlcov
	rm -rf .coverage

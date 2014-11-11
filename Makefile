#!/usr/bin/env make

# Makefile: because we need more elaborate commands than manage.py

# The target names are not a file produced by the commands of that target. Always out of date.
.PHONY: clean e2e unit test data cov odsimport doc install_script npm gulp

# Install in current directory
install_script:
	./install.sh

# Install everything: Django requirements, the DB, node packages, and
# build the app.
install:  install_script npm gulp

# Install npm and bower packages
npm:
	@echo "Installing Node and bower packages..."
	npm install
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
	./manage.py test search

# Run test of an independent module.
ods:
	cd search/datasources/odslookup/tests/ && nosetests --nologcapture

# Run all tests possible.
test: unit e2e ods

# Install the app in a fresh environment
ci:
	source ci-testing.sh

# Load sample data, for testing purposes.
data:
	./manage.py loaddata dumpdata

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

clean:
	find . -name "*.pyc" -exec rm {} +
	rm -rf htmlcov
	rm -rf .coverage

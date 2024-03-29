#!/usr/bin/env make

# Makefile: because we need more elaborate commands than manage.py

# The target names are not a file produced by the commands of that target. Always out of date.
.PHONY: clean unit test data cov odsimport doc install_script npm gulp tox migrations shell

all: qa unit

clone:
	git clone --recursive https://gitlab.com/vindarel/abelujo.git

# System dependencies to install as root on Debian (Ubuntu/LinuxMint):
debian-nosudo:
	@grep -v "^#" abelujo/apt-requirements.txt | xargs apt-get install -y
	pip install virtualenvwrapper

debian:
	@grep -v "^#" abelujo/apt-requirements.txt | xargs sudo apt-get install -y
	@sudo pip install virtualenvwrapper

pull:
	git stash save "autostash from make publl"
	git pull --rebase
	git submodule update --remote

# Install in current directory
pip: pip-submodule
	@pip install -r abelujo/requirements.txt     # install python libraries locally

pip-nosudo: pip-submodule
	@pip install -r abelujo/requirements.txt

pip-dev:
	@pip install -r abelujo/requirements-dev.txt # other python libs, for development

pip-submodule:
	cd search/datasources && python setup.py install

pip-submodule-dev:
	cd search/datasources && pip install -r requirements-dev.txt

# deprecated when all clients are above bookshops v0.9. Should be in late 2020.
pip-uninstall-previous-libs:
	@pip uninstall -y bookshops  # around v0.9, an installed "bookshops" lib will hide newer code.


db:
	@python manage.py syncdb --noinput           # populate the db for django
	@python manage.py loaddata dbfixture.json    # set required card types and default place.

dbback:
	# back up the db, append a timestamp
	bash -c "cp db.db{,.`date +%Y%m%d-%H%M%S`}"

# Install everything: Django requirements, the DB, node packages, and
# build the app.
install:  debian pip pip-submodule db translation-compile collectstatic

# xxx: there must be a better way (to do the same task with and without sudo)
install-nosudo:  debian-nosudo pip-nosudo db collectstatic translation-compile

install-dev:  debian pip pip-dev pip-submodule pip-submodule-dev db npm npm-dev gulp translation-compile

# Install npm packages
npm-system:
	@echo "Installing gulp globally... (needs root)"
	@sudo npm install -g gulp@3

npm-system-nosudo:
	@echo "Installing gulp globally... (needs root)"
	npm global install gulp

npm:
	@echo "Installing Node packages..."
	mkdir -p public
	npm install --production # don't install devDependencies
	# Saving dev ip for gunicorn
	echo "localhost" > IP.txt

npm-dev:
	npm install # not in production, install also devDependencies

set-prod:
	touch PROD.txt

stash:
	git stash save "update (probably stashing npm lock)"

update: stash
	make pull
	# make set-prod  # issues with serving the PDF bills… (2021-08 still)
	make pip
	make pip-submodule
	make migrate
	# Get code, install new packages, run DB migrations, compile JS and translation files.
	make collectstatic
	make translation-compile 	# gunicorn needs a restart
	# echo "it's good to do an apt-get update once in a while"  # prevents unreachable sources, sometimes.
	@echo "For development, don't forget make pip-dev. To update Debian dependencies, use make update-apt."

update-code: stash
	make pull
	make migrate
	make collectstatic
	make translation-compile
	make gunicorn-restart

update-dev: update pip-dev pip-submodule-dev npm-dev

# Create migrations and commit them.
migrations:
	python manage.py makemigrations
	git add search/migrations/*.py

migrate:
	python manage.py migrate --noinput

collectstatic:
	mkdir -p public
	python manage.py collectstatic --noinput

# Run the tests of the UI in a browser.
livescript: search/tests/integration-tests/*.ls
	# compile livescript files
	cd search/tests/integration-tests/ && lsc -c *.ls

end2end:
	# it was buggy on Firefox (waiting for async/await ?).
	testcafe chromium search/tests/integration-tests/testcafetest.js

# Build static files
gulp:
	gulp

# Run the dev server
run:
	python manage.py runserver 8000

run_plus:
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


gunicorn-restart:
	kill -HUP $(shell cat PID.txt)

gunicorn: run-gunicorn

shell:
	python manage.py shell_plus

# Define processes in the Procfile.
taskqueue:
	honcho start &

# run only unit tests.
unit:
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

send_test_emails:
	./manage.py test search.tests.noci_tests_api_stripe.TestLive.notest_send_test_emails

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
	coverage run --source='search/' \
		manage.py test search.tests --pattern="tests_*.py"
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

doc:
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
	django-admin.py makemessages -d djangojs --ignore="doc/dev/_build/*" --ignore="static/js/build/vendor.js" --ignore="static/lib/*" --ignore="node_modules/*" --ignore="bootstrap/*" --ignore="admin/js/*" --ignore="collectedstatic/*" -a

translation-compile:
	django-admin.py compilemessages 	# gunicorn needs a restart




###########################################################
# QA
###########################################################

flake8:
	flake8 --config=setup.cfg abelujo search *.py

mccabe:
	python -m mccabe --min 10 search/models/models.py
	python -m mccabe --min 10 search/models/api.py

qa: flake8

pylint:
	pylint abelujo search

###########################################################
# Cleanup
###########################################################
uninstall-js:
	@echo "##### Removing local JS libraries..."
	rm -rf node_modules/
	@echo "  done."
	@echo "##### Uninstalling nodejs..."
	sudo apt-get remove nodejs npm

uninstall-pip:
	@echo "This depends on how you created the python virtual env."
	@echo "If you used mkvirtualenv, do"
	@echo "\t rmvirtualenv abelujo"
	@echo "Otherwise, delete abelujo/bin/ or ~/.venvs/abelujo or ~/.virtualenvs/abelujo."

uninstall-python:
	@echo "We don't see why you would need this :]"
	@echo "You shouldn't remove python from your system, it is used by many other applications."

uninstall:
	@echo "See these subcommands: uninstall-js, uninstall-pip (and uninstall-python)."
	@echo "You can remove the abelujo directory afterwards."

clean:
	find . -name "*.pyc" -exec rm {} +
	rm -rf htmlcov
	rm -rf .coverage

clean-caches:
	# that can be needed when moving scraper code.
	find . -name "cache.sqlite" -exec rm {} +

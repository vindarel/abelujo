#!/bin/bash

# Create and activate a virtualenv
# http://virtualenvwrapper.readthedocs.org/en/latest/

export WORKON_HOME=~/.venvs
[[ -d $WORKON_HOME ]] || mkdir -p $WORKON_HOME
source /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv abelujo-ci

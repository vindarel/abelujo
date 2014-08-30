#!/bin/bash

# Get the project, create the env, install the dependencies, the db
# and launch tests.
# It uses the branch master (it will ignore edits not commited).

# We need to source venv_create so we need to record the working directory.
abelujo=$(pwd)
venv=${VIRTUAL_ENV##*/}  # strip out the path

cd /tmp
# rm -rf abelujo-test
mkdir abelujo-test
cd abelujo-test
git init
git remote add origine /home/vince/projets/ruche-web/abelujo/.git
git pull origine master
source venv_create.sh
./install.sh
make unit

cd $abelujo
workon $venv

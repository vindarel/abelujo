#!/bin/bash
# Copyright 2014 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

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

#!/bin/bash
# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

# Create and activate a virtualenv
# http://virtualenvwrapper.readthedocs.org/en/latest/

# if no argument given, set the env name.
VENV_NAME=${1:-abelujo}
export WORKON_HOME=~/.venvs
[[ -d $WORKON_HOME ]] || mkdir -p $WORKON_HOME
# source /usr/local/bin/virtualenvwrapper.sh
echo "source virtualenvwrapper.sh: "
source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
# Install with access to system packages,
# for some are too big and long to install and don't need to be that up to date (xml, pillow, ...)
echo "mkvirtualenv: "
mkvirtualenv $VENV_NAME --system-site-packages
echo "did mkvirtualenv"

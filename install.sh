#!/bin/bash

# Install Abelujo, the easiest way as possible.
# Usage: right clic, run this script in a terminal.
# Supposed to be in a directory that does not already contain an Abelujo/ folder.

LOCALHOST=http://localhost:8000
VENV=abelujo


venv_activate () {
    source bin/activate
}

run_and_open () {
    (make run &
    make gulp
    sleep 3 && xdg-open $LOCALHOST)
}

if [[ -d abelujo ]] ; then
    cd abelujo
    venv_activate
    run_and_open

else
    echo "********* Installing Abelujo...                                       *********"
    echo "********* (if you cloned this repository, no need to use this script.)*********"
    git clone --recursive http://gitlab.com/vindarel/abelujo/ || (echo "The installation failed. Feel free to email us the results." ; exit 1)

    cd abelujo
    echo "*******************************************************************************"
    echo "*********  Please type your administrator password               **************"
    echo "*********  (it is normal not to see the characters you type !)   **************"
    echo "-------------------------------------------------------------------------------"
    echo "--------- Veuillez entrer votre mot de passe super-utilisateur   --------------"
    echo "--------- (c'est normal de ne pas voir ce que l'on tape !)       --------------"
    echo "-------------------------------------------------------------------------------"
    # let's go. We test the installation on CI, don't we ?!
    make debian
    make install
    sudo make install-nodejs
    virtualenv ./
    source bin/activate
    pip install --upgrade pip
    make install
    run_and_open

fi

read  # let the terminal waiting, so open, in case of error.

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

help_sudo_password () {
    echo "*******************************************************************************"
    echo "*********  Please type your administrator password               **************"
    echo "*********  (it is normal not to see the characters you type !)   **************"
    echo "-------------------------------------------------------------------------------"
    echo "--------- Veuillez entrer votre mot de passe super-utilisateur   --------------"
    echo "--------- (c'est normal de ne pas voir ce que l'on tape !)       --------------"
    echo "-------------------------------------------------------------------------------"
}

install_git () {
    type git || help_sudo_password && sudo apt-get install -qy git-core
}


if [[ -d abelujo ]] ; then
    echo "Running current Abelujo version. You may want to update (cd abelujo ; make update)."
    pwd
    ls abelujo
    cd abelujo
    virtualenv ./ && \
    venv_activate && \
    run_and_open

else
    echo "********* Installing Abelujo...                                       *********"
    echo "********* (if you cloned this repository, no need to use this script.)*********"
    install_git
    git clone --recursive http://gitlab.com/vindarel/abelujo/ || (echo "The installation failed. Feel free to email us the results." ; exit 1)

    cd abelujo
fi

    sudo apt install -yq make
    help_sudo_password

    sudo make install-yarn
    make debian && \
    virtualenv ./ && \
    source bin/activate && \
    sudo make install-nodejs && \
    sudo pip install --upgrade pip && \
    make install && \
    run_and_open


read  # let the terminal waiting, so open, in case of error.
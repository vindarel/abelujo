#!/bin/bash

# Install Abelujo, the easiest way as possible.
# Usage: right clic, run this script in a terminal.
# Supposed to be in a directory that does not already contain an Abelujo/ folder.

LOCALHOST=http://localhost:8000
VENV=abelujo-venv


venv_activate () {
    source bin/activate
}

buildjs_and_run () {
    make gulp && \
        make run
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
    type git || ( help_sudo_password && sudo apt-get install -qy git-core )
}


ensure_cloned_sources () {
  if [[ -d abelujo ]] ; then
      echo "Running current Abelujo version. You may want to update (cd abelujo ; make update)."
      pwd
      ls abelujo
      cd abelujo
      virtualenv ./ && \
      venv_activate && \
      make update && \
      buildjs_and_run

  else
      echo "********* Installing Abelujo...                                       *********"
      echo "********* (if you cloned this repository, no need to use this script.)*********"
      install_git
      git clone --recursive http://gitlab.com/vindarel/abelujo/
  fi
}

ensure_cloned_sources && \
    cd abelujo && \
    help_sudo_password && \
    sudo apt install -yq make && \
    make debian && \
    virtualenv ./ && \
    source bin/activate && \
    make install && \
    buildjs_and_run

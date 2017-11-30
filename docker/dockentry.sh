#!/bin/bash
#
# Create a "docker" user with sudo rights, in order to test our
# installation script in real conditions, and run it.
#
# Run with
# chmod +x dockentry.sh
# Files in docker/ directory, to be able to clone in abelujo/.
# docker run  -v /home/vince/projets/ruche-web/abelujo/docker:/home/docker/ -ti ubuntu:16.04 /home/docker/dockentry.sh
#
# Install missing sudo
echo "---- Installing sudo..."
apt update && apt install -qy sudo

adduser --disabled-password --gecos '' docker
adduser docker sudo
echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# run installation script.
echo "----- Install ------"
pwd
# warning: docker/install.sh was copied.
su -m docker -c "cd /home/docker/ && /home/docker/install.sh"

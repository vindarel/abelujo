Continuous Integration
======================

We use gitlab CI. See `.gitlab-ci.yml`.


Testing the installation script on Docker
-----------------------------------------

See `docker/dockentry.sh` and `docker/install.sh`.

The first one creates a sudo user and runs the second one.

Given you have Docker already installed, run the installation script
in a fresh Ubuntu 16:04 with::

  chmod +x dockentry.sh
  docker run  -v "$(pwd)/docker":/home/docker/ -ti ubuntu:16.04 /home/docker/dockentry.sh


`-v` mounts the files in the current directory into docker's home
(user `docker`). `-i` is for interactive section. The final argument
runs the given script (to create the sudo user etc).

You can also step into the image with simply `-ti ubuntu:16.04`, and
run bits of scripts manually from there.

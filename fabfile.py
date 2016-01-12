#!/usr/bin/env python

HELP = """This file is a fabric: http://docs.fabfile.org/en/latest/

We declare commands to manage remotely through ssh our Abelujo
instances, there on a remote server.

Utilities are in fabutils.py
Here, a method == a fab command.
Note: see Task instances of fabric 1.1.

We rely on a file called clients.yaml. This file as this kind of structure:

url: <url or IP adress of the server>
home: /home/yourusername
user: <user name to login to the server>
venv: <default virtual environment. Each client should have its own>
dir: <default directory path where all the clients live>

clients:
  - name: demo
    port: 8000
    venv: demo

  - name: next
    port: 8005
    venv: next

Available commands:

- fab update:<name of client>

  it will ssh to the server, cd to the client's repository, activate
the virtualenv and update Abelujo.

- fab check_uptodate:<name of client>

  tells by how many commits the projects are behind master.

- fab statusall

   checks and prints the status of all clients.

TODO: restart gunicorn when needed. It can be needed to load new
templatetags, to load new translations,...

"""

import os
import sys
from subprocess import check_output

import addict
from termcolor import colored

from fabric.api import cd
from fabric.api import env
from fabric.api import prefix
from fabric.api import run

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fabutils import select_client_cfg, get_yaml_cfg

CLIENTS = "clients.yaml"

cfg = get_yaml_cfg(CLIENTS)
cfg = addict.Dict(cfg)

env.hosts = cfg.url
env.user = cfg.user

# Notes:

            # with quiet():
    # have_build_dir = run("test -e /tmp/build").succeeded

# When used in a task, the above snippet will not produce any run:
# test -e /tmp/build line, nor will any stdout/stderr display, and
# command failure is ignored.

# env.parallel http://docs.fabfile.org/en/latest/usage/env.html#env-parallel
# http://docs.fabfile.org/en/latest/usage/parallel.html

def help():
    print HELP

def odsimport(odsfile=None):
    """Import cards from a LibreOffice calc. See its doc.
    """
    cmd = 'make odsimport odsfile={}'.format(odsfile)

def statusall():
    for client in cfg.clients:
        check_uptodate(client.name)

def check_uptodate(client):
    """Check wether the distant repo is up to date with the local one. If
    not, how many commits behind ?

    """
    max_count = 10

    cfg = CLIENTS
    cfg = get_yaml_cfg(cfg)
    cfg = addict.Dict(cfg)
    client = select_client_cfg(client, cfg)
    wd = cfg.home + cfg.dir + client.name + "/abelujo"
    git_head = check_output(["git", "rev-parse", "HEAD"]).strip()
    with cd(wd):
        res = run("git rev-parse HEAD")
        # print "commit of {} is {}".format(wd, res)

        if res == git_head:
            print colored("- {} is up to date".format(client.name), "green")
        else:
            git_last_commits = check_output(["git", "rev-list", "HEAD", "--max-count={}".format(max_count)]).split("\n")
            if res in git_last_commits:
                index = git_last_commits.index(res)
                print "- {} is ".format(wd) +\
                    colored("{}", "red").format(index) +\
                    " commits behind"
            else:
                print colored("- {}", "blue").format(client.name) +\
                    " is more than " +\
                    colored("{}", "red").format(max_count) +\
                    " commits behind."

def update(client):
    """Update a client.

    - client: name, or part of name of a client (str). We'll get the
    client's full name.

    TODO: sometimes, we need to restart the server (for django to load
    a new module like templatetags, for translations,...).

    """
    cfg = CLIENTS
    cfg = get_yaml_cfg(cfg)
    cfg = addict.Dict(cfg)
    client = select_client_cfg(client, cfg)
    wd = cfg.home + cfg.dir + client.name + "/abelujo"
    with cd(wd):
        with prefix("source ~/.virtualenvs/{}/bin/activate".format(client.venv)):
            res = run("make update")

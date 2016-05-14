#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from fabric.api import execute
from fabric.api import prefix
from fabric.api import put
from fabric.api import run
from fabric.api import sudo
from fabric.contrib.files import exists
from fabutils import get_yaml_cfg
from fabutils import select_client_cfg

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

CLIENTS = "clients.yaml"

CFG = get_yaml_cfg(CLIENTS)
CFG = addict.Dict(CFG)
VENV_SOURCE = "source ~/.virtualenvs/{}/bin/activate"
#: the gunicorn command: read the port from PORT.txt, write the pid to PID.txt (so as to kill it).
#: Live reload on code change.
GUNICORN = "gunicorn --env DJANGO_SETTINGS_MODULE={project_name}.settings {project_name}.wsgi --bind={url}:$(cat PORT.txt) --reload --pid PID.txt"
env.hosts = CFG.url
env.user = CFG.user

CLIENT_TMPL = """

  - name: {}
    venv: {}
    port: {}
"""

# Use ssh_config for passwords and cie
# env.use_ssh_config = True

# Notes:

            # with quiet():
    # have_build_dir = run("test -e /tmp/build").succeeded

# When used in a task, the above snippet will not produce any run:
# test -e /tmp/build line, nor will any stdout/stderr display, and
# command failure is ignored.

# env.parallel http://docs.fabfile.org/en/latest/usage/env.html#env-parallel
# http://docs.fabfile.org/en/latest/usage/parallel.html

# Take inspiration from Mezzanine: https://github.com/stephenmcd/mezzanine/blob/master/mezzanine/project_template/fabfile.py

def help():
    print HELP

def odsimport(odsfile=None):
    """Import cards from a LibreOffice calc. See its doc.
    """
    cmd = 'make odsimport odsfile={}'.format(odsfile)

def statusall():
    for client in CFG.clients:
        check_uptodate(client.name)

def openclient(client):
    """Open the client page with a web browser.
    """
    client = select_client_cfg(client, CFG)
    cmd = "firefox {}:{}/fr/ & 2>/dev/null".format(CFG.url, client.port)
    os.system(cmd)

def check_uptodate(client=None):
    """Check wether the distant repo is up to date with the local one. If
    not, how many commits behind ?

    """
    max_count = 10

    if not client:
        return statusall()

    client = select_client_cfg(client, CFG)
    wd = os.path.join(CFG.home, CFG.dir, client.name, CFG.project_name)
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
                print colored("- {}", 'blue').format(client.name) +\
                    " is " +\
                    colored("{}", "yellow").format(index) +\
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

    TODO: sometimes, we need to restart the server: to load new
    templates, for django to load a new module like templatetags, for
    translations,....

    """
    cfg = CLIENTS
    cfg = get_yaml_cfg(cfg)
    cfg = addict.Dict(cfg)
    client = select_client_cfg(client, cfg)
    wd = os.path.join(cfg.home, cfg.dir, client.name, CFG.project_name)
    with cd(wd):
        run("echo {} > PORT.txt".format(client.port))
        with prefix(VENV_SOURCE.format(client.venv)):
            res = run("make update")

def ssh_to(client):
    config = CFG
    client = select_client_cfg(client, CFG)
    cmd = "ssh -Y {}@{}".format(config.get('user'),
                                   client.get('url', config.get('url')))
    if config.get('dir') or client.get('dir'):
        cmd += " -t 'cd {}; zsh --login;'".format(
            os.path.join(config.get('home'),
                         config.get('dir', client.get('dir')),
                         client.get('name'),
                         CFG.project_name),)
    print "todo: workon venv"
    print "connecting to {}".format(cmd)
    os.system(cmd)

def create():
    """Create a new client and call the install task.

    - name: name of the client (and of the venv).
    """
    name = raw_input("Client name ? ")
    venv = raw_input("Venv name ? [{}] ".format(name))
    venv = venv or name
    # Get the first available port
    ports = [it.port for it in CFG.clients]
    ports = sorted(ports)
    possible_ports = range(8000, 8000 + len(CFG.clients) + 1)
    free_port = list(set(possible_ports) - set(ports))[0]
    port = raw_input("Port ? [{}] ".format(free_port))
    port = port or free_port

    # Write into the config file
    with open(CLIENTS, "a") as f:
        f.write(CLIENT_TMPL.format(name, venv, port))
        execute(install(name))

def copy_files(name, *files):
    """
    """
    client = select_client_cfg(name, CFG)
    tmp_init_data = '/tmp/{}/'.format(client.name)
    if not exists(tmp_init_data):
        run('mkdir -p {}'.format(tmp_init_data))
    put(files[0], tmp_init_data)

def install(name):
    """Clone and install Abelujo into the given client directory.

    Create a super user,

    populate the DB with initial data, if any,

    run gunicorn with the right port.
    """
    client = select_client_cfg(name, CFG)
    wd = CFG.home + CFG.dir + client.name
    if not exists(wd):
        run("mkdir {}".format(wd, wd))
    with cd(wd):
        run("test -d {} || git clone {}".format(CFG.project_name, CFG.project_git_url))
        with cd(CFG.project_name):
            import ipdb; ipdb.set_trace()
            # TODO:
            # - create a venv
            # - install,
            # run('make install')
            # - create super user
            # - populate DB with initial data if any
            # The csv files may be in nested directories.
            run('make odsimport odsfile=$(find /tmp/{}/*csv)'.format(client.name))
            # - run gunicorn with the right port,


def start(name):
    """Run gunicorn.

    Read the port in PORT.txt
    """
    client = select_client_cfg(name, CFG)
    wd = CFG.home + CFG.dir + client.name
    with cd(wd):
        with prefix(VENV_SOURCE.format(client.name)):
            gunicorn = GUNICORN.format(project_name=CFG.project_name, url=CFG.url)
            print "TODO: run in background"
            run(gunicorn)

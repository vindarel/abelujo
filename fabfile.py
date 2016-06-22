#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from subprocess import check_output

import addict
import requests
import termcolor

from fabric.api import cd
from fabric.api import env
from fabric.api import execute
from fabric.api import prefix
from fabric.api import put
from fabric.api import run
from fabric.api import sudo
from fabric.contrib.files import exists
import fabutils

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
CLIENTS = "clients.yaml"

CFG = fabutils.get_yaml_cfg(CLIENTS)
CFG = addict.Dict(CFG)
VENV_ACTIVATE = "source ~/.virtualenvs/{}/bin/activate"
#: the gunicorn command: read the port from PORT.txt, write the pid to PID.txt (so as to kill it).
#: Live reload on code change.
GUNICORN = "gunicorn --env DJANGO_SETTINGS_MODULE={project_name}.settings {project_name}.wsgi --bind={url}:$(cat PORT.txt) --reload --pid PID.txt --daemon"
env.hosts = CFG.url
env.user = CFG.user

#: timeout (in s) for http requests
TIMEOUT = 15

CLIENT_TMPL = """

  - name: {}
    venv: {}
    port: {}
"""

#: pretty console output
COL_WIDTH = 10

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

def openclient(client):
    """Open the client page with a web browser.
    """
    client = fabutils.select_client_cfg(client, CFG)
    cmd = "firefox {}:{}/fr/ & 2>/dev/null".format(CFG.url, client.port)
    os.system(cmd)

def statusall():
    for client in CFG.clients:
        check_uptodate(client.name)

def check_uptodate(client=None):
    """Check wether the distant repo is up to date with the local one. If
    not, how many commits behind ?

    """
    max_count = 10

    if not client:
        return statusall()

    client = fabutils.select_client_cfg(client, CFG)
    wd = os.path.join(CFG.home, CFG.dir, client.name, CFG.project_name)
    git_head = check_output(["git", "rev-parse", "HEAD"]).strip()
    with cd(wd):
        res = run("git rev-parse HEAD")
        # print "commit of {} is {}".format(wd, res)

        if res == git_head:
            print termcolor.colored("- {} is up to date".format(client.name), "green")
        else:
            git_last_commits = check_output(["git", "rev-list", "HEAD", "--max-count={}".format(max_count)]).split("\n")
            if res in git_last_commits:
                index = git_last_commits.index(res)
                print termcolor.colored("- {}", 'blue').format(client.name) +\
                    " is " +\
                    termcolor.colored("{}", "yellow").format(index) +\
                    " commits behind"
            else:
                print termcolor.colored("- {}", "blue").format(client.name) +\
                    " is more than " +\
                    termcolor.colored("{}", "red").format(max_count) +\
                    " commits behind."

def _request_call(url):
    status = 0
    try:
        status = requests.get(url, timeout=TIMEOUT).status_code
    except Exception as e:
        # print "Exception: {}".format(e)
        status = 404

    return status

def check_online(client=None):
    """Check every instance's working.

    Parallel task on same host with multiprocessing (fabric does on /different/ hosts).
    """

    if not client:
        sorted_clients = sorted(CFG.clients, key=lambda it: it.name)
    else:
        sorted_clients = [fabutils.select_client_cfg(client, CFG)]

    urls = ["http://{}:{}/fr/".format(CFG.url, client.port) for client in sorted_clients]

    import multiprocessing
    pool = multiprocessing.Pool(8)

    status = pool.map(_request_call, urls)
    res = zip(status, sorted_clients)
    for status, client in res:
        if status != 200:
            print termcolor.colored(u"- {:{}} has a pb".format(client.name, COL_WIDTH), "red") + " on {}".format(client['port'])
        else:
            print u"- {:{}} ".format(client.name, COL_WIDTH) + termcolor.colored("ok", "green")


def save_port(name):
    """Save the port nb into the file port.txt
    """
    client = fabutils.select_client_cfg(name, CFG)
    wd = os.path.join(CFG.home, CFG.dir, client.name, CFG.project_name)
    with cd(wd):
        run("echo {} > PORT.txt".format(client.port))

def update(client):
    """Update a client.

    - client: name, or part of name of a client (str). We'll get the
    client's full name.

    TODO: sometimes, we need to restart the server: to load new
    templates, for django to load a new module like templatetags, for
    translations,....

    """
    client = fabutils.select_client_cfg(client, CFG)
    wd = os.path.join(CFG.home, CFG.dir, client.name, CFG.project_name)
    with cd(wd):
        save_port(client.name)
        with prefix(VENV_ACTIVATE.format(client.venv)):
            res = run("make update")

    check_online(client.name)

def ssh_to(client):
    client = fabutils.select_client_cfg(client, CFG)
    cmd = "ssh -Y {}@{}".format(CFG.get('user'),
                                   client.get('url', CFG.get('url')))
    if CFG.get('dir') or client.get('dir'):
        cmd += " -t 'cd {}; zsh --login;'".format(
            os.path.join(CFG.get('home'),
                         CFG.get('dir', client.get('dir')),
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
    exists = fabutils.select_client_cfg(name, CFG, quiet=True)
    if exists:
        print "Client {} already exists (venv {} and port {}). Abort.".format(name, exists['venv'], exists['port'])
        exit(1)

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
    client = fabutils.select_client_cfg(name, CFG)
    tmp_init_data = '/tmp/{}/'.format(client.name)
    if not exists(tmp_init_data):
        run('mkdir -p {}'.format(tmp_init_data))
    put(files[0], tmp_init_data)

def create_venv(venv):
    """Create a new venv.
    """
    run('virtualenv ~/.virtulanves/{}'.format(venv))

def install(name):
    """Clone and install Abelujo into the given client directory.

    Create a super user,

    populate the DB with initial data, if any,

    run gunicorn with the right port.
    """
    client = fabutils.select_client_cfg(name, CFG)
    client = addict.Dict(client)
    wd = CFG.home + CFG.dir + client.name
    if not exists(wd):
        run("mkdir {}".format(wd, wd))
    with cd(wd):
        run("test -d {} || git clone --recursive {}".format(CFG.project_name, CFG.project_git_url))
        # save the port
        save_port(client.name)
        with cd(CFG.project_name):
            # - create a venv
            create_venv(client.venv)
            with prefix(VENV_ACTIVATE.format(client.venv)):
                # TODO:
                # - install,
                run('make install')
            # - create super user
            # - populate DB with initial data if any
            # The csv files may be in nested directories.
            # run('make odsimport odsfile=$(find /tmp/{}/*csv)'.format(client.name))
            # - run gunicorn with the right port,
                start(client.name)

def start(name):
    """Run gunicorn.

    Read the port in PORT.txt
    """
    client = fabutils.select_client_cfg(name, CFG)
    wd = CFG.home + CFG.dir + client.name + "/abelujo"
    with cd(wd):
        print wd
        with prefix(VENV_ACTIVATE.format(client.name)):
            gunicorn = GUNICORN.format(project_name=CFG.project_name, url=CFG.url)
            run(gunicorn)

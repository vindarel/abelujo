#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import os
import sys
from subprocess import check_output

import addict
import pendulum
import requests
import termcolor
from fabric.api import cd
from fabric.api import env
from fabric.api import prefix
from fabric.api import put
from fabric.api import run
from fabric.api import settings
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
templatetags, to load new translations, to load submodules python code...

"""
CLIENTS = "clients.yaml"

CFG = fabutils.get_yaml_cfg(CLIENTS)
CFG = addict.Dict(CFG)
VENV_ACTIVATE = "source ~/.virtualenvs/{}/bin/activate"
#: the gunicorn command: read the port from PORT.txt, write the pid to PID.txt (so as to kill it).
#: Live reload on code change.
GUNICORN = "gunicorn --env DJANGO_SETTINGS_MODULE={project_name}.settings {project_name}.wsgi --bind={url}:$(cat PORT.txt) --reload --pid PID.txt --daemon"
#: File name whith the port number
PID_FILE = "PID.txt"
#: Kill a server instance
CMD_KILL = "kill -9 $(cat {})".format(PID_FILE)

#: Command to rebase a repo
CMD_REBASE = "make rebase"

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

#: Date format (appending to backed up files)
DATE_FORMAT = "%Y%m%d-%H:%M:%S"

BOWER_COMPONENTS_TAR = "bower_components.tar.gz"
BOWER_COMPONENTS_DIR = "static/bower_components"
BOWER_COMPONENTS_REMOTE_DIR = "/tmp/bower_components"
BOWER_COMPONENTS_REMOTE = "/tmp/bower_components.tar.gz"

# Use ssh_config for passwords and cie
# env.use_ssh_config = True

# Notes:

# with quiet():
#     have_build_dir = run("test -e /tmp/build").succeeded

# When used in a task, the above snippet will not produce any run:
# test -e /tmp/build line, nor will any stdout/stderr display, and
# command failure is ignored.

# env.parallel http://docs.fabfile.org/en/latest/usage/env.html#env-parallel
# http://docs.fabfile.org/en/latest/usage/parallel.html

# Take inspiration from Mezzanine: https://github.com/stephenmcd/mezzanine/blob/master/mezzanine/project_template/fabfile.py

def help():
    print(HELP)

def odsimport(odsfile=None):
    """Import cards from a LibreOffice calc. See its doc.
    """
    # cmd = 'make odsimport odsfile={}'.format(odsfile)
    raise NotImplementedError

def openclient(client=None):
    """Open the client page with a web browser.
    """
    if not client:
        print("Usage: openclient:<part of client name>")
        client_info()
        exit(0)

    client = fabutils.select_client_cfg(client, CFG)
    cmd = "firefox {}:{}/fr/ & 2>/dev/null".format(CFG.url, client.port)
    os.system(cmd)

def client_info(name=None):
    """Show a client info (which port does he use ?). By default, show all.

    Prints to stdout.
    """
    if name:
        client = fabutils.select_client_cfg(name)
        print(client)

    else:
        for it in sorted(CFG.clients):
            fabutils.print_client(it)

def statusall():
    for client in CFG.clients:
        check_uptodate(client.name)

def check_uptodate(name=None):
    """Check wether the distant repo is up to date with the local one. If
    not, how many commits behind ?

    """
    max_count = 1000
    acceptable_count = 10

    if not name:
        return statusall()

    client = fabutils.select_client_cfg(name, CFG)
    if not client:
        print("No client found with '{}'".format(name))
        return 1
    wd = os.path.join(CFG.home, CFG.dir, client.name, CFG.project_name)
    # that's local so it conuts the unpushed commits. should be remote
    git_head = check_output(["git", "rev-parse", "HEAD"]).strip()

    with cd(wd):
        res = run("git rev-parse HEAD")
        tag = run("git describe --tags")
        if res == git_head:
            print(termcolor.colored("- {} is up to date".format(client.name), "green"))
        else:
            last_commit_date = check_output(["git", "show", "-s", "--format=%ci", res])
            acceptable_trailing_by = check_output(["git", "rev-list", "HEAD", "--max-count={}".format(acceptable_count)]).split("\n")
            git_last_commits = check_output(["git", "rev-list", "HEAD", "--max-count={}".format(max_count)]).split("\n")
            index = git_last_commits.index(res)
            if res in acceptable_trailing_by:
                print(termcolor.colored("- {}", 'blue').format(client.name) +
                    " is " +
                    termcolor.colored("{}", "yellow").format(index) +
                      " commits behind. Head is at: {}, {} ({})".format(
                          tag, last_commit_date, res))
            else:
                print(termcolor.colored("- {}", "blue").format(client.name) +
                    " is  " +
                    termcolor.colored("{}", "red").format(index) +
                      " commits behind. Head is at: {}, {} ({})".format(
                          tag, last_commit_date, res))

def _request_call(url):
    status = 0
    try:
        status = requests.get(url, timeout=TIMEOUT).status_code
    except Exception:
        # print("Exception: {}".format(e))
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

    urls = ["http://{}:{}/fr/".format(CFG.url, c.port) for c in sorted_clients]

    import multiprocessing
    pool = multiprocessing.Pool(8)

    status = pool.map(_request_call, urls)
    res = zip(status, sorted_clients)
    for status, client in res:
        if status != 200:
            print(termcolor.colored("- {:{}} has a pb".format(client.name, COL_WIDTH), "red") + " on {}".format(client['port']))
        else:
            print("- {:{}} ".format(client.name, COL_WIDTH) + termcolor.colored("online", "green"))
def _save_variables(name):
    """
    Another def for multiprocessing. Functions can only be pickled if they are at the toplevel.
    """
    if name:
        client = fabutils.select_client_cfg(name)
        wd = os.path.join(CFG.home, CFG.dir, client.name, CFG.project_name)
        ip = client.get('ip', CFG.ip)
        sentry_token = CFG.get('sentry_token')
        with cd(wd):
            run("echo {} > PORT.txt".format(client.port))
            run("echo {} > IP.txt".format(ip))
            run("echo {} > sentry.txt".format(sentry_token))

    else:
        print("_save_variables: give a name as argument.")

def save_variables(name=None):
    """Save some directory-specific variables into their txt files:

    - the port nb into the file port.txt
    - the ip into IP.txt (for gunicorn)
    - the Sentry token into sentry.txt
    """

    if name:
        _save_variables(name)

    else:
        yesno = raw_input("Set port and ip for all clients ? [Y/n]")
        if not yesno or fabutils.yes_answer(yesno):
            import multiprocessing
            pool = multiprocessing.Pool(8)
            sorted_clients = sorted(CFG.clients, key=lambda it: it.name)
            names = [it.name for it in sorted_clients]
            pool.map(_save_variables, names)

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
        save_variables(client.name)
        with prefix(VENV_ACTIVATE.format(client.venv)):
            run("make update")

    # check_online(client.name) # wait a bit before to check

def updatelight(name=None):
    """
    Everything except package managers (apt, npm, pip).
    """
    if not name:
        print("Please give a client as argument.")
        exit(1)
    client = fabutils.select_client_cfg(name, CFG)
    wd = os.path.join(CFG.home, CFG.dir, client.name, CFG.project_name)
    with cd(wd):
        make('update-code', client.name)

    print("Client updated: {}".format(client))

def updateverylight(name=None):
    """
    Only pull new code, submodule included. Don't run migrations, don't build JS.
    """
    if not name:
        print("Give a client name as argument.")
        exit(1)
    client = fabutils.select_client_cfg(name, CFG)
    wd = os.path.join(CFG.home, CFG.dir, client.name, CFG.project_name)
    with cd(wd):
        make('pull', client.name)
        print("Client updated (pull): {}".format(client))

def dbback(name=None):
    """Copy the db file locally (there), appendding a timestamp, and download it.
    Only for users marked in production in clients.yaml.
    """
    if not name:
        clients = sorted(CFG.clients)

    else:
        clients = [fabutils.select_client_cfg(name)]

    if not name:
        # Only for prod:
        clients = filter(lambda it: it.status == "prod", clients)
    print(termcolor.colored(
        "Backup for {} users in prod: {}.".format(
            len(clients),
            map(lambda it: it.name, clients)),
        "yellow"))

    for client in clients:
        ip = client.ip or CFG.ip
        user = client.user or CFG.user
        env.user = user
        with settings(host_string=ip):
            with cd(fabutils.wd(client, CFG)):
                # Copy locally. Append a timestamp.
                run("cp db.db{,.`date +%Y%m%d-%H%M%S`}")

                # Download
                db_backed = "backup/db-{}-{}.sqlite".format(client.name, pendulum.datetime.now().strftime(DATE_FORMAT))
                ip = client.ip or CFG.ip
                cmd = "rsync -av {user}@{url}:/home/{user}/{dir}/{client_name}/{project_name}/{db_name} ./{db_backed}".format(
                    user=client.user or CFG.user,
                    url=ip,
                    dir=CFG.dir.strip("/"),
                    client_name=client.name,
                    project_name=CFG.project_name,
                    db_name=CFG.db_name,
                    db_backed=db_backed
                )

                print("Downloading db of user {}".format(termcolor.colored("{}".format(client.name), "blue")))
                print(cmd)
                os.system(cmd)

def bundles_upload():
    """Update, but don't run npm or bower, get the copies of their
    directories (node_modules and bower_components).

    Goal: win a few minutes, don't depend on npmjs, and *don't be
    surprised by new mismatches*.

    Beware, Work In Progress.
    Still to do:
    - check if our npm/bower dependencies changed, compared to what is currently uploaded
    """

    if not exists(BOWER_COMPONENTS_REMOTE_DIR):
        run("mkdir {}".format(BOWER_COMPONENTS_REMOTE_DIR))

    # The remote destination will be the same as our local source.
    needs_bundle = fabutils.bundle_needs_update()
    if needs_bundle:
        cmd = "rsync -av --delete {dir} {user}@{url}:/tmp/".format(
            user=CFG.user,
            url=CFG.url,
            dir=BOWER_COMPONENTS_DIR,
        )
        os.system(cmd)

def bundles_deploy(name):
    """After bundle_up, we have them in /tmp/.
    Now, simply copy them into our client's static/bower_components or node_modules.
    """
    client = fabutils.select_client_cfg(name)
    fabutils.wd(client, CFG)

    if not exists(BOWER_COMPONENTS_REMOTE_DIR):
        print("Error: we can't find the bower components directory in remote /tmp.")
        return

    client_dir = os.path.join(CFG.home, CFG.dir, client.name, CFG.project_name, "static")
    if not exists(client_dir):
        run("mkdir -p {}".format(client_dir))

    run("cp -r {} {}".format(BOWER_COMPONENTS_REMOTE_DIR, client_dir))

def rebase(name=None):
    """Only run git rebase. That may be enough for light updates.
    (but be careful nothing breaks !)

    Rebase the given client, or all simultaneously.

    xxx: check if the pip requirements, the js sources or xxx changed
    and update what's needed (try not to run apt, pip and npm every
    time).
    """
    def do_rebase(client):
        wd = os.path.join(CFG.home, CFG.dir, client.name, CFG.project_name)
        with cd(wd):
            with prefix(VENV_ACTIVATE.format(client.venv)):
                run(CMD_REBASE)

    if name:
        client = fabutils.select_client_cfg(name)
        do_rebase(client)

        check_online(name)

def ssh_to(client):
    client = fabutils.select_client_cfg(client, CFG)
    ip = client.get('ip') or CFG.get('ip')
    user = client.get('user') or CFG.get('user')
    cmd = "ssh -Y {}@{}".format(user, ip)
    if CFG.get('dir') or client.get('dir'):
        cmd += " -t 'cd {}; zsh --login;'".format(
            os.path.join("/home/{}".format(user),
                         CFG.get('dir', client.get('dir')),
                         client.get('name'),
                         CFG.project_name),)
    print("todo: workon venv")
    print("connecting to {}".format(cmd))
    os.system(cmd)

def port_info(nb=0):
    """Whose port is that ?
    """
    if nb:
        try:
            nb = int(nb)
        except Exception:
            print("{} is a number ?".format(nb))
            return

        clt = fabutils.whose_port(nb, CFG)
        for cl in clt:
            print(termcolor.colored(cl.name, "blue"),)
            print("\t (venv: " + cl.venv + ")")

    else:
        for it in sorted(CFG.clients, key=lambda it: it.port):
            fabutils.print_client(it)

def create(name=None):
    """Create a new client and call the install task.

    - name: name of the client (and of the venv).
    """
    if not name:
        name = raw_input("Client name ? ")
    exists = fabutils.select_client_cfg(name, quiet=True)
    if exists:
        print("Client {} already exists (venv {} and port {}). Abort.".format(name, exists['venv'], exists['port']))
        exit(1)

    venv = name
    # Get the first available port
    ports = [it.port for it in CFG.clients if it.port]
    ports.append(8000)
    ports.append(8001)
    ports = sorted(ports)
    possible_ports = range(8000, 8000 + len(CFG.clients) + 1)
    free_port = list(set(possible_ports) - set(ports))[0]
    port = raw_input("Port ? [{}] ".format(free_port))
    port = port or free_port
    if int(port) in ports:
        print("Error: this port is taken.")
        exit(1)

    # Write into the config file
    with open(CLIENTS, "a") as f:
        f.write(CLIENT_TMPL.format(name, venv, port))

    install(name)

def file_upload(name, *files):
    """
    Upload the given file(s) to this client's directory root.
    """
    if not files:
        print("Usage: file_upload:name,path-to-file")
        exit(1)

    client = fabutils.select_client_cfg(name)
    tmp_init_data = '/tmp/{}/'.format(client.name)
    if not exists(tmp_init_data):
        run('mkdir -p {}'.format(tmp_init_data))
    put(files[0], tmp_init_data)

def create_venv(venv):
    """Create a new venv.
    """
    run('virtualenv ~/.virtualenvs/{}'.format(venv))

def install(name):
    """Clone and install Abelujo into the given client directory.

    Create a super user,

    populate the DB with initial data, if any,

    run gunicorn with the right port.
    """
    client = fabutils.select_client_cfg(name)
    client = addict.Dict(client)
    wd = os.path.join(CFG.home, CFG.dir, client.name)
    if not exists(wd):
        run("mkdir {}".format(wd, wd))

    # Copy bower_components (experimental)
    bundles_upload()

    with cd(wd):
        run("test -d {} || git clone --recursive {}".format(CFG.project_name, CFG.project_git_url))
        bundles_deploy(client.name)
        # save the port
        save_variables(client.name)
        with cd(CFG.project_name):
            # - create a venv
            create_venv(client.venv)
            with prefix(VENV_ACTIVATE.format(client.venv)):
                # - install,
                run('make install')
                # TODO:
            # - create super user
            # - populate DB with initial data if any
            # The csv files may be in nested directories.
            # run('make odsimport odsfile=$(find /tmp/{}/*csv)'.format(client.name))
            # - run gunicorn with the right port,
                start(client.name)

def stop(name):
    """Stop the gunicorn process found in the pid file.
    """
    client = fabutils.select_client_cfg(name)
    with cd(fabutils.wd(client, CFG)):
        if exists(PID_FILE):
            run(CMD_KILL)
            run("rm {}".format(PID_FILE))

def start(name):
    """Run gunicorn (daemon).

    Read the port in PORT.txt
    """
    client = fabutils.select_client_cfg(name)
    with cd(fabutils.wd(client, CFG)):
        with prefix(VENV_ACTIVATE.format(client.name)):
            gunicorn = GUNICORN.format(project_name=CFG.project_name, url=CFG.url)
            run(gunicorn)

def restart(name):
    """
    Send a restart signal to gunicorn.
    """
    cmd = "gunicorn-restart"
    make(cmd, name)


def make(cmd, name=None):
    """Run any make command remotevy
    """
    if name:
        client = fabutils.select_client_cfg(name)
        with cd(fabutils.wd(client, CFG)):
            with prefix(VENV_ACTIVATE.format(client.name)):
                run("make {}".format(cmd))

    else:
        print("fab make: no client name given")

def cmd(cmd, name=None):
    """Run any command to client "name".
    """
    if not name:
        print("Please give a client name.")
    else:
        client = fabutils.select_client_cfg(name)
        with cd(fabutils.wd(client, CFG)):
            with prefix(VENV_ACTIVATE.format(client.name)):
                run(cmd)


def script(script, name=None):
    """
    Run script `script` to client `name`.
    """
    if not name:
        print("Please give a client name.")
        return
    # client = fabutils.select_client_cfg(name)
    com = "python manage.py runscript {}".format(script)
    cmd(com, name)


def bower_package_version(package, names=None):
    """What's the installed packages version ?

    - package: bower package name
    - names: list of client names (or only beginning of name, as usual).
    """
    # usage = "Usage: fab bower_package_version:package,client"

    #: With --json, we could parse it and get rid off the sub-deps
    BOWER_PACKAGE_VERSION = './node_modules/bower/bin/bower list --offline'

    if not names:
        clients = CFG.clients

    else:
        name = names[0]
        clients = [fabutils.select_client_cfg(name)]

    for client in clients:
        wd = os.path.join(CFG.home, CFG.dir, client.name, CFG.project_name)
        print(wd)
        with cd(wd):
            run(BOWER_PACKAGE_VERSION)

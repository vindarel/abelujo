#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import difflib
import filecmp
import os
import sys

import addict
import termcolor
import yaml

CLIENTS = "clients.yaml"

def get_yaml_cfg(afile):
    """From a yaml file, return the yaml structure.
    """
    data = None
    if os.path.isfile(afile):
        with open(afile, "r") as f:
            txt = f.read()

        data = yaml.load(txt)

    return data

def select_client_cfg(letters, quiet=False):
    """Get the client that matches the letters given as argument.

    exple: select_client("loc") will select localhost.

    return: the client's configuration dictionnary.
    """
    cfg = get_yaml_cfg(CLIENTS)
    cfg = addict.Dict(cfg)

    clients = cfg.clients
    cl = filter(lambda it: it.name.startswith(letters), clients)
    if len(cl) > 1:
        print("Found more than one possible clients, can't decide: {}".format([it.name for it in cl]))
        return []
    if not cl:
        if not quiet:
            print("No client found with '{}'".format(sys.argv[1]))
            print("existing clients:")
            print([it.name for it in cfg.clients])
            exit(1)
        return []
    return cl[0]

def whose_port(number, cfg):
    """
    """
    clients = cfg.clients
    clt = filter(lambda it: it.port == number, clients)
    if len(clt) > 1:
        print("Warning ! Many clients have the same port number")
    return clt

def _print_status(status):
    if not status:
        return "?"
    if "abandoned" in status:
        return termcolor.colored(status, "red")
    if "staling" in status:
        return termcolor.colored(status, "yellow")
    if "prod" in status:
        return termcolor.colored(status, "blue")
    return status

def print_client(client):
    print(termcolor.colored("- {:15} ".format(client.name), "blue") + "\t {}".format(client.port) + "\t{}".format(_print_status(client.status)))

def wd(client, cfg):
    """Get the working directory.
    """
    cfg = get_yaml_cfg(CLIENTS)
    cfg = addict.Dict(cfg)
    return os.path.join(cfg.home, cfg.dir, client.name, cfg.project_name)

def bundle_needs_update():
    """Were the package.json and bower.json modified since last time we
    uploaded our bundled js dependencies ?

    Simply check if these files changed, against a cached version.

    Note: uneeded ? We rely on rsync.

    Return: bool
    """
    ret = False
    package_json = "package.json"
    bower_json = "bower.json"
    package_cache = "package.json.bundlecache"
    bower_cache = "bower.json.bundlecache"

    # The caches exist ?
    if not os.path.exists(package_cache):
        print(termcolor.colored("package.json has no cache, so we don't know if it changed since last upload. Need rebuild.", "yellow"))
        ret = True
    if not os.path.exists(bower_cache):
        print(termcolor.colored("bower.json has no cache, so we don't know if it changed since last upload. Need rebuild.", "yellow"))
        ret = True
    if ret:
        return True

    # Do the files look different ?
    ret = False
    if not filecmp.cmp(package_json, package_cache):
        print(termcolor.colored("package.json seems to have changed", "yellow"))
        package_lines = open(package_json, "r").readlines()
        package_cache_lines = open(package_cache, "r").readlines()
        diff = difflib.unified_diff(package_cache_lines, package_lines)
        diff_print(diff)
        ret = True  # they don't seem equal, they need an update

    if not filecmp.cmp(bower_json, bower_cache):
        print(termcolor.colored("bower.json seems to have changed", "yellow"))
        ret = True

        bower_lines = open(bower_json, "r").readlines()
        bower_cache_lines = open(bower_cache, "r").readlines()
        diff = difflib.unified_diff(bower_cache_lines, bower_lines)
        diff_print(diff)

    return ret

def diff_print(generator):
    """Colorful print.
    - generator: given by unified diff
    """
    for line in generator:
        if line.startswith("-"):
            print(termcolor.colored(line, "red"))
        elif line.startswith("+"):
            print(termcolor.colored(line, "green"))
        else:
            print(line)

def yes_answer(answer):
    """
    """
    return answer in ["Y", "y", "yes", "O", "o"]

def main():
    cfg_file = "clients.yaml"
    cfg = get_yaml_cfg(cfg_file)
    cfg = addict.Dict(cfg)
    client = select_client_cfg(sys.argv[1], cfg)
    ssh_to(client, config=cfg)


if __name__ == "__main__":
    exit(main())

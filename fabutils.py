#!/usr/bin/env python

import os
import sys

import addict
import yaml

def get_yaml_cfg(afile):
    """From a yaml file, return the yaml structure.
    """
    data = None
    if os.path.isfile(afile):
        with open(afile, "r") as f:
            txt = f.read()

        data = yaml.load(txt)

    return data

def select_client_cfg(letters, cfg):
    """Get the client that matches the letters given as argument.

    exple: select_client("loc") will select localhost.

    return: the client's configuration dictionnary.
    """
    clients = cfg.clients
    cl = filter(lambda it: it.name.startswith(letters), clients)
    if len(cl) > 1:
        print "Found more than one possible clients, can't decide: {}".format([it.name for it in cl])
        return []
    if not cl:
        print "Nobody found with '{}'".format(sys.argv[1])
        print "existing clients:"
        print [it.name for it in cfg.clients]
        exit(1)
    return cl[0]

def main():
    cfg_file = "clients.yaml"
    cfg = get_yaml_cfg(cfg_file)
    cfg = addict.Dict(cfg)
    client = select_client_cfg(sys.argv[1], cfg)
    ssh_to(client, config=cfg)

if __name__ == "__main__":
    exit(main())

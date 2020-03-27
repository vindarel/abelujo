#!/bin/env python
# -*- coding: utf-8 -*-

import json
import tqdm

from search.datasources.frFR.librairiedeparis import librairiedeparisScraper

"""Read some json, take the cards not found, search them with a
Scraper, save to another json in order to run odsimport.py once again.

Run this script with runscript:

    ./manage.py runscript notfound_retry.py --script-args <path to json file(s)>

"""

DEST_JSON = "notfound_retried.json"

def missing(fn, source=None):
    """Read the given json, read the cards not found, search for them.

    - fn: file name
    - source: datasource module

    return: list of cards (dict)
    """
    with open(fn, 'r') as f:
        data = json.load(f)
    not_found = data.get('cards_not_found')
    cards = []

    for card in tqdm.tqdm(not_found):
        scraper = source.Scraper(card.get('ISBN'))
        res, errors = scraper.search()
        cards += res

    return cards

def save_to_file(item, path=DEST_JSON):
    """Write data to path.
    """
    with open(path, "w") as f:
        raw = json.dumps(item)
        f.write(raw)

def run(*args):
    """args with --script-args

    give json files
    """
    cards = []
    for i, fil in enumerate(args):
        print("---------------")
        print("Importing file {}/{}: {}".format(i + 1, len(args), fil))
        print("---------------")
        res = missing(fil, source=librairiedeparisScraper)
        cards += res

    # save the cards found
    save_to_file({'cards_found': cards})
    print("All done.")

#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

import csv
from unidecode import unidecode
import logging
import os
import sys
from subprocess import call
from toolz import valmap

import clize
from sigtools.modifiers import annotate
from sigtools.modifiers import autokwoargs

from odsutils import getMissingData
from odsutils import keysEqualValues
from odsutils import setRowTypes
from odsutils import translateHeader
from odsutils import translateAllKeys
from odsutils import removeDuplicates
from odsutils import removeVoidRows
from odsutils import replaceAccentsInStr


"""
Goal: import the cards listed in a LibreOffice Calc sheet (.ods).

Different solutions:

- parse the odt file with the odfpy library. I.e., read every cell
  with xml-style methods and return a python data structure.
  - pros: total control, full python
  - cons: more code than the other solutions, code that needs a lot of
    unit tests, bad documentation. My first atempt worked well until
    encountering a first misbehaviour.
- ask the user to give a csv file and parse it with the builtin csv
  library.
  - cons: we want this feature to be dead simple for the user.
- convert the ods file to csv with a LibreOffice shell command,
  soffice. [method adopted]
  - pro: simple. Very little code required.
  - cons: LibreOffice dependency. How bad is it for a server ?

If in the csv column the distributor isn't set, it is supposed to be the publisher.

"""

# logging.basicConfig(format='%(levelname)s [%(funcName)s] %(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

def convert2csv(odsfile):
    """Convert an ods file (LibreOffice Calc) to csv.
    """
    cmd = ["soffice", "--headless", "--convert-to", "csv"]
    cmd.append(odsfile)
    ret = call(cmd)
    if ret == 0:
        return os.path.splitext(odsfile)[0] + ".csv"
    else:
        return None

def fieldNames(csvfile):
    """Return the field names of the file.
    They may not be at the first row.

    If there is no field names, read a config file ("odssettings.py")
    where they are specified.

    return a tuple (original fieldnames, translated fieldnames).

    """
    settings = "odssettings.py"

    with open(csvfile, "r") as f:
        csvdata = f.read()
    data = csvdata.splitlines()
    # We expect that a row with "title" is the row with all field names.
    for i, line in enumerate(data):
        if "TITLE" in line.upper() or "TITRE" in line.upper():
            orig_fieldnames = line
            fieldnames = [translateHeader(orig_fieldnames.split(",")[ind]) for ind in range(len(orig_fieldnames.split(",")))]
            fieldnames = map(lambda x: x.upper(), fieldnames)
            return orig_fieldnames, fieldnames

    # No field names ? Read a config file.
    if os.path.isfile(settings):
        try:
            from odssettings import fields
            fields = map(lambda x: x.upper(), fields)
            csvfields = ",".join(fields)
            return csvfields, fields
        except Exception as e:
            log.error("Error while trying to import the field names from the odssettings.py file: {}".format(e))

    log.info("warning: no fieldnames found in file {}.".format(csvfile))
    return [], []

def extractCardData(csvfile, lang="frFR", nofieldsrow=False, delimiter=";"):
    """Return the interesting data.

    The fieldnames may not be the first row. Skip the useless lines,
    find the fieldnames and re-read the csv.

    Requirements: a row will be taken into account if it has a title
    and a publisher (TITRE et EDITEUR).

    return: a dictionnary with:
    - fieldnames: the list of fieldnames
    - data: the list of cards
    - messages: a list of messages, that are dictionnaries with
      "message" and "level" fields (error, warning, etc).

    """
    fieldnames = data = None
    messages = []
    to_ret = {"fieldnames": fieldnames, "data": data, "messages": messages, "status": 0}
    orig_fieldnames, fieldnames = fieldNames(csvfile)
    if "TITLE" not in fieldnames and "ISBN" not in fieldnames:
        msg = "Erreur: nous n'avons pas trouvé la colonne %s" % ("TITRE",)  # TODO translate
        to_ret["messages"].append({"message": msg, "level": "error"})
        to_ret["status"] = 1
    if "PUBLISHERS" not in fieldnames and "ISBN" not in fieldnames:
        msg = "Erreur: nous n'avons pas trouvé la colomne %s" % ("EDITEUR",)
        to_ret["messages"].append({"message": msg, "level": "error"})
        to_ret["status"] = 1
    if to_ret["status"] == 1:
        return to_ret

    # data = filter(lambda line: len(line) != len(fieldnames), data)
    reader = csv.DictReader(open(csvfile, "r"),
                            fieldnames=orig_fieldnames.split(","),
                            delimiter=delimiter)

    # skip the lines untill we find the fieldnames one.
    if not nofieldsrow:
        while not keysEqualValues(reader.next()):
            pass
    rest = [line for line in reader]
    # XXX: should validate data. We may not have the wright delimiter, and so on.

    # Translate all keys to english. How to do it before ? We prefer not to rewrite the csv file.
    data = translateAllKeys(rest)
    data = removeVoidRows(data)
    if "TITLE" in fieldnames:
        data = removeDuplicates(data)
    # replace accents bad encoding.
    data = map(lambda dic: valmap(replaceAccentsInStr, dic), data)
    data = setRowTypes(data)
    # Usually, if distributor is not set then it is the publisher.
    data = getMissingData(data)
    return {"fieldnames": fieldnames, "data": data, "messages": messages}

def run(odsfile, nofieldsrow=False):
    """
    :param str odsfile: the .ods file
    """
    csvdata = []
    csvfile = convert2csv(odsfile)
    if os.path.exists(csvfile):
        csvdata = extractCardData(csvfile, nofieldsrow=nofieldsrow)
        if csvdata["data"]:
            # print "found data:", csvdata["data"]
            print "results found in CSV: ", len(csvdata["data"])
        else:
            if csvdata["messages"]:
                log.info("\n".join(msg["message"] for msg in csvdata["messages"]))
            else:
                log.info("warning: no suitable data was found in file. Do nothing.")

    else:
        log.error("The csv file doesn't exist, there was an error with its conversion.\
        Hint: close all LibreOffice windows before continuing.")
    return csvdata


@annotate(sourcefile=clize.Parameter.REQUIRED)
@autokwoargs
def main(sourcefile, nofieldsrow=False):
    """
    Read a source file (ods, csv) and return its rows as a python dict, each row mapped to its column name.

    nofieldsrow: use if the ods/csv file has only columns of data and
       not a row of field names. In that case, use the odssettings.py config file to read the field names.

    """
    run(sourcefile, nofieldsrow=nofieldsrow)

if __name__ == '__main__':
    exit(clize.run(main))

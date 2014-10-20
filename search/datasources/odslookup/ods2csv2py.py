#!/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
import sys
from subprocess import call
from toolz import valmap

from odsutils import keysEqualValues
from odsutils import translateHeader
from odsutils import translateAllKeys
from odsutils import removeVoidRows


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

"""

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

def replaceAccentsInStr(string):
    # This is aweful.
    # We could ignore remaining ones with encode("utf8", "ignore").
    return string.replace("�","é").replace("�", "ç")\
        .replace("�", "'").replace("�", "à").replace("�", "è").replace("�", "ê")

def fieldNames(csvfile):
    """Return the field names of the file.
    They may not be at the first row.

    return a tuple (original fieldnames, translated fieldnames).
    """
    with open(csvfile, "r") as f:
        csvdata = f.read()
    data = csvdata.splitlines()
    for i, line in enumerate(data):
        if "TITLE" in line.upper() or "TITRE" in line.upper():
            orig_fieldnames = line
            fieldnames = [translateHeader(orig_fieldnames.split(",")[ind]) for ind in range(len(orig_fieldnames.split(",")))]
            fieldnames = map(lambda x: x.upper(), fieldnames)
            return orig_fieldnames, fieldnames
    print "warning: no fieldnames found in file {}.".format(csvfile)
    return [], []

def extractCardData(csvfile, lang="frFR"):
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
    if "TITLE" not in fieldnames:
        msg = "Erreur: nous n'avons pas trouvé la colomne %s" % ("TITRE",)  # TODO translate
        to_ret["messages"].append({"message": msg, "level": "error"})
        to_ret["status"] = 1
    if "PUBLISHER" not in fieldnames:
        msg = "Erreur: nous n'avons pas trouvé la colomne %s" % ("EDITEUR",)
        to_ret["messages"].append({"message": msg, "level": "error"})
        to_ret["status"] = 1
    if to_ret["status"] == 1:
        return to_ret
    # data = filter(lambda line: len(line) != len(fieldnames), data)
    reader = csv.DictReader(open(csvfile, "r"), fieldnames=orig_fieldnames.split(","))
    # skip the lines untill we find the fieldnames one.
    while not keysEqualValues(reader.next()):
        pass
    rest = [line for line in reader]
    # Translate all keys to english. How to do it before ? We prefer not to rewrite the csv file.
    data = translateAllKeys(rest)
    # TODO: manage lower/upper case
    data = removeVoidRows(data)
    # replace accents bad encoding.
    data = map(lambda dic: valmap(replaceAccentsInStr, dic), data)
    return {"fieldnames": fieldnames, "data": data, "messages": messages}

def run(odsfile):
    """
    :param str odsfile: the .ods file
    """
    csvdata = []
    csvfile = convert2csv(odsfile)
    if os.path.exists(csvfile):
        csvdata = extractCardData(csvfile)
        if csvdata["data"]:
            print "found data:", csvdata["data"]
            print "results found: ", len(csvdata["data"])
        else:
            if csvdata["messages"]:
                print "\n".join(msg["message"] for msg in csvdata["messages"])
            else:
                print "warning: no suitable data was found in file. Do nothing."

    else:
        print "error with csv conversion."
    return csvdata

def main():
    if len(sys.argv) > 1:
        odsfile = sys.argv[1]
        run(odsfile)
    else:
        print "Missing an argument."
        print "Usage: %s calcsheet.ods" % (sys.argv[0],)

if __name__ == '__main__':
    exit(main())

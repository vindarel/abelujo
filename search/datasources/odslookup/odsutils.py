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

from unidecode import unidecode
from toolz import itemmap
from toolz import keymap


def cleanText(tag):
    return unidecode(tag.strip().strip(":")) # see rmPunctuation

def translateHeader(tag, lang="frFR", to="enEN"):
    """The ods file will be in whatever language possible and the data
    retrieved from the scrapers are dictionnaries with english field
    names. We need the same in both.

    takes a tag and returns its translation (english by default).
    """
    if lang == "frFR":
        if "TITRE" in cleanText(tag.upper()):
            return "title"
        elif "PRIX" in tag.upper():
            return "price"
        elif cleanText(tag.upper()) in ["AUTEUR",]:
            return "authors"  # mind the plurial
        elif cleanText(tag).upper() in ["EDITEUR", "ÉDITEUR", u"ÉDITEUR"]: # warning utf8 !
            return "publisher"
        elif "DIFFUSEUR" in cleanText(tag).upper():
            return "distributor"
        elif "REMISE" in cleanText(tag).upper():
            return "discount"
        elif "STOCK" in cleanText(tag).upper():
            return "quantity"
        else:
            # print "translation to finish for ", tag
            return tag
    elif lang.startswith("en"):
        if cleanText(tag.upper()) in ["TITLE",]:
            return "TITLE"
    else:
        print "todo: others header translations"

    return tag

def translateAllKeys(data):
    """
    :param list of dict data: list of dictionnaries.
    """
    # keymap: apply function to keys of dictionnary.
    return map(lambda dic: keymap(translateHeader, dic), data)

def toInt(val):
    """
    """
    try:
        val = int(val)
    except Exception as e:
        return 0
    return val

def toFloat(val):
    """safely cast to float."
    """
    # can't django accept strings ?
    try:
        val = val.replace(',', '.')
        val = float(val)
    except Exception as e:
        # print "Error getting an int of {}: {}".format(val, e)
        return 0
    return val

def giveTagType(item):
    key = item[0]
    val = item[1]
    if key.upper() == "PRICE":
        val = toFloat(val)
    elif key.upper() == "DISCOUNT":
        val = val.strip('%')
        val = toFloat(val)

    return key, val

def setRowTypes(data):
    """
    :param list of dict data:
    """
    return map(lambda dic: itemmap(giveTagType, dic), data)

def _getMissingData(dic):
    if dic.get('publisher') and not dic.get('distributor'):
        dic['distributor'] = dic.get('publisher')

    return dic

def getMissingData(data):
    """
    :param list of dict
    """
    return map(_getMissingData, data)

def keysEqualValues(dic):
    """check that all keys are equal to their value.
    We have "title": "title" etc.
    """
    return all(map(lambda tup: tup[0] == tup[1], zip(dic.keys(), dic.values())))

def removeVoidRows(data):
    """Remove rows for which the title or the publisher is the null string.
    """
    data = filter(lambda line: (line["title"] != "") and (line["publisher"] != ""), data)
    return data

def replaceAccentsInStr(string):
    """Replace non printable utf-8 characters with their printable
    equivalent. Because the csv module doesn't fully support utf8
    input ! All input should be utf8 printable.

    Fortunately, a web query to our datasources will still return the
    right result, they deal corretly with accent issues.

    cf https://docs.python.org/2/library/csv.html

    """
    string = string.strip('?') # do also some cleanup: see rmPunctuation
    return unidecode(string)

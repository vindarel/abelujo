#!/bin/env python
# -*- coding: utf-8 -*-

from toolz import keymap


def translateHeader(tag, lang="frFR", to="enEN"):
    """The ods file will be in whatever language possible and the data
    retrieved from the scrapers are dictionnaries with english field
    names. We need the same in both.

    takes a tag and returns its translation (english by default).
    """
    def cleanText(tag):
        return tag.strip().strip(":")

    if lang == "frFR":
        if cleanText(tag.upper()) in ["TITRE",]:
            return "title"
        elif tag.upper() in ["PRIX",]:
            return "price"
        elif cleanText(tag.upper()) in ["AUTEUR",]:
            return "authors"  # mind the plurial
        elif cleanText(tag) in ["editeur", "EDITEUR", "ÉDITEUR", u"\xe9diteur"]: # warning utf8 !
            return "publisher"
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

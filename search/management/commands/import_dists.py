#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.
"""
Import a csv file of distributors, created from a Dilicom document.
"""
from __future__ import print_function
from __future__ import unicode_literals

import tqdm
from django.core.management.base import BaseCommand

from search.models import Distributor

def find_separator(line, default=None):
    if ";" in line:
        return ";"
    if "," in line:
        return ","
    return default

class Command(BaseCommand):

    help = "Import a csv file."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        """
        Import distributors, set their GLN and address.
        """
        import os
        csvfile = "documents/annuaire_distributeurs.csv"

        if not os.path.exists(csvfile):
            print("The required file {} doesn't exist. Can not import distributors.".format(csvfile))
            exit(1)

        csvdate = "02/06/2020"  # creation date by Dilicom
        columns = "GLN DISTRIBUTEUR;RAISON SOCIALE DISTRIBUTEUR;CODE POSTAL;VILLE;PAYS;NB TITRES FEL;COMM. VIA DILICOM"
        # COMM. VIA DILICOM can be: "N" "O"
        # There are actually quite a lot of countries:
        # ("PAYS" "POLOGNE" "AFRIQUE DU SUD" "LAOS" "ALGERIE" "EGYPTE" "ITALIE"
        # "PORTUGAL" "COMORES" "AUTRICHE" "TCHEQUE (REPUBLIQUE)"
        # "NLLE CALEDONIE - FRANCE" "MAURICE (ILE)" "GRECE" "LIBAN" "BENIN"
        # "MAYOTTE - FRANCE" "HAITI" "FINLANDE" "SENEGAL" "HONG-KONG" "BURKINA" "ISRAEL"
        # "EMIRATS ARABES UNIS" "THAILANDE" "GUADELOUPE - FRANCE"
        # "CONGO (REPUBLIQUE DEM.)" "ROYAUME UNI" "REUNION - FRANCE" "ETATS UNIS"
        # "POLYNESIE FRANC. - FRANCE" "RWANDA" "" "LUXEMBOURG" "MAROC" "CROATIE"
        # "GUYANE - FRANCE" "CANADA" "ROUMANIE" "INDE" "CHINE" "ALLEMAGNE" "AUSTRALIE"
        # "MONACO" "MALTE" "COTE D'IVOIRE" "ESPAGNE" "TUNISIE" "MARTINIQUE - FRANCE"
        # "BELIZE" "FRANCE" "BELGIQUE" "SUISSE")

        # XXX: deal with utf8 in py2 and py3.
        with open(csvfile, "r") as f:
            lines = f.readlines()

        lines = [it.strip() for it in lines]

        separator = find_separator(lines[0], default=";")

        existing_GLNs = Distributor.objects.values_list("gln", flat=True)

        try:
            for i, line in tqdm.tqdm(enumerate(lines)):
                gln, name, postal_code, city, country, nb_titles, via_dilicom = line.split(separator)
                if gln in existing_GLNs:
                    dist = Distributor.objects.get(gln=gln)
                else:
                    dist = Distributor(gln=gln)

                dist.name = name
                dist.postal_code = postal_code
                dist.city = city
                dist.country = country
                dist.nb_titles_in_FEL = nb_titles
                dist.comm_via_dilicom = via_dilicom

                dist.save()

        except KeyboardInterrupt:
            self.stdout.write("Abort.")

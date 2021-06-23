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

from __future__ import unicode_literals

import os

import pendulum

LINE_A = "A0001{gencode_destinataire}"
LINE_B = "B0002{gencode_commande_par}"
LINE_C = "C0003{numero_commande}"  # must be unique for 1 year
LINE_D = "D0004{date}"
LINE_E = "E0005{mode_expedition: lieu habituel, PRISME… }{code_notation}"  # et code remise-déla, date livraison au plus tôt/au plus tard
# Ligne G optionnelle ? cf exemple.
LINE_G = "G{line_nb}{type_commande}"  # line_nb: 0006 si line_e, sinon 0005.
LINE_L = "L{line_nb}{ean13}{quantite_6_chars}"  # quantité sur 6 charactères, complétés par des 0
LINE_Q = "Q{line_nb}"

#: We command to Dilicom, which does the work to dispatch by distributor.
# Otherwise, we should send one command file per distributor.
DILICOM_GENCODE = "3035593037000"
DILICOM_GENCODE_TEST = "3015593010100"


class ValidationError(BaseException):
    pass


def valid_line_l(line):
    if not line:
        return False
    return len(line) == 24 and line.startswith('L')

def valid_ean13(ean):
    return len(ean) == 13

def valid_txt(txt):
    messages = []
    lines = txt.split('\n')
    length = len(lines)
    q_line = lines[-1]

    if not (txt.startswith('A0001') or txt.startswith(u'A0001')):
        messages.append("doesn't start with A00001")
    if not len(q_line) == 5:
        messages.append("the Q line is not of length 6")
    if not q_line.startswith('Q') or int(q_line[1:]) != length:
        messages.append("The Q line doesn't refer to the file length")
    if messages:
        raise ValidationError("\n\n".join(messages))
    return True

def format_line_nb(i):
    "Format on 4 characters"
    return "{:04}".format(i)

def get_date():
    """
    AAAAMMJJ
    """
    now = pendulum.now()
    res = now.format('%Y%m%d')
    assert len(res) == 8
    return res

def format_quantity(nb):
    """
    Format on 6 characters.
    """
    return "{:06}".format(nb)

def get_user_gln():
    res = os.getenv('DILICOM_USER')
    if not res:
        raise "No bookshop GLN found. Set it in DILICOM_USER."
    if len(res) != 13:
        print('WARN: the GLN {} seems wrong.'.format(res))
    return res

def get_ftp_username():
    return os.getenv('DILICOM_FTP_USER') or os.getenv('DILICOM_FTP_USERNAME')

def get_ftp_password():
    return os.getenv('DILICOM_PASSWORD')

def get_gencode_destinataire(test=False):
    """
    Get the bookshop GLN or the Dilicom test (DILICOM_TEST is set).
    """
    if test or os.getenv('DILICOM_TEST'):
        print("INFO: using Dilicom's test GLN")
        return DILICOM_GENCODE_TEST

    return DILICOM_GENCODE

def generate_internet_format(basketcopies):
    # TODO: from Command
    """
    Generate the text to send as a file to Dilicom's FTP.

    - basketcopies: list of BasketCopies objects, containing quantity: the quantity to command, and the Card object with card.isbn.

    A0001<gencode destinataire/distributeur>
    B0002<gencode du "commandé par">
    C0003<numéro de la commande>
    D0004<date>
    E0005<mode d'expédition: lieu habituel, PRISME…> <code notation: 0 règle habituelle>
    G0005 (car pas de présence de ligne G) (type de commande, rappel référence)
    L0006<ean><quantité>
    L0007 etc
    Qxxxx = nbr de lignes de A à Q.
    """
    lines = []
    exceptions = []
    gencode_destinataire = get_gencode_destinataire()
    a_line = LINE_A.format(gencode_destinataire=gencode_destinataire)
    b_line = LINE_B.format(gencode_commande_par=get_user_gln())

    numero_commande = "000100"  # TODO: Command.pk
    c_line = LINE_C.format(numero_commande=numero_commande)

    d_line = LINE_D.format(date=get_date())

    e_line = "E0005090"  # mode d'expédition = livraison habituelle, code notation = habituel.
    # Spécifier Prisme ?
    # Les distributeurs ne tiennent pas compte en général des codes utilisés dans les
    # commandes EDI. Le mode d’expédition et la notation dépendent plutôt de ce qui a
    # été négocié au moment de l’ouverture du compte.

    # g_line = None

    lines += [a_line, b_line, c_line, d_line, e_line]

    offset = 1 + len(lines)  # control the line nb of subsequent L lines.
    for i, bc in enumerate(basketcopies):
        i += offset
        ean13 = bc.card.isbn
        if not valid_ean13(ean13):
            exceptions.append("Invalid EAN13: {}".format(ean13))
        line = LINE_L.format(line_nb=format_line_nb(i),
                             ean13=ean13,
                             quantite_6_chars=format_quantity(bc.quantity),
                             )
        if not valid_line_l(line):
            exceptions.append("Invalid line L: {}".format(line))
        lines.append(line)

    q_line = LINE_Q.format(line_nb=format_line_nb(len(lines) + 1))
    lines.append(q_line)

    if exceptions:
        print(exceptions)
        exit(1)

    txt = "\n".join(lines)
    print(txt)
    assert valid_txt(txt), "The final TXT is not valid. Find out why !"
    return txt


if __name__ == "__main__":
    from search import models
    user = get_ftp_username()
    password = get_ftp_password()
    gln = get_user_gln()
    if not user or not password:
        print("WARN: no Dilicom FTP username or password found.")
    generate_internet_format(models.Basket.auto_command_copies())

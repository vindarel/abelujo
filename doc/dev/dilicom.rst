Working with Dilicom
====================

Abelujo supports the "FEL à la demande par web service" by Dilicom.

Abelujo nearly supports passing commands automatically to Dilicom.

The bookshop must subscribe to Dilicom's paying service. Choose:

- FEL à la demande par web service
- format des commandes: format text plat.

You will receive new credentials. They are different from the user's
credentials for Dilicom's user web client.

*As of 2021, we are working on the "FEL complet format Onix".*

Additional data
---------------

Dilicom provides much more data than Abelujo's scrapers. You will find:

- publisher
- distributor GLN (Abelujo maps the GLN to its name)
- CLIL theme
- collection
- présentation éditeur (broché, présentoir etc)
- dimensions (height, width, thickness)
- weight
- price details (VAT etc)
- market availability
- can we command the book with Dilicom?
- more…


Missing data
------------

These data are not available in the FEL à la demande, only in the "FEL complet Onix":

- cover image
- summary
- number of pages

Start Abelujo with Dilicom credentials
--------------------------------------

  DILICOM_USER=GLN DILICOM_PASSWORD=bar make gunicorn


Working with the API
--------------------

``/api/card/:id?with_dilicom_update=1`` returns the book data, and calls
Dilicom to update data (the price, the publisher, the
distributor…). Dilicom messages are returned in
`alerts.dilicom_update`. If the ISBN was not found on Dilicom, the
card object gets `dilicom_unknown_ean` set to True (it is normally
false).

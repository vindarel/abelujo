User documentation
==================

Preferences
-----------

In admin, Preferences, you can choose:

* the **default place**: to which place a book you register goes by
  default (you can move copies once they are registered).


Compatibility
-------------

The forms are best rendered with Firefox >= 29 (the integer form
fields are not rendered with the html5 "number" widget but with a less
practical text widget on precedent versions).


Import cards from a LibreOffice Calc sheet (.ods)
-------------------------------------------------

This is possible only on the command line at the moment.

Your sheet must have the columns "title" and "publisher". Those are
the two columns the script will use to fire a query on your favorite
datasource.

Type::

    make odsimport src="yourfile.ods"
    # which is a shortcut for:
    # python manage.py runscript odsimport.py --script-args yourfile.ods

You will see a verbose output. The script will:

* parse your ods file and find a list of cards with their respective information,
* for each of them, fire a query to the datasource on the title and the publisher,
* check and filter the results against your data,
* sort the fetched data into three groups: the cards found, the ones found but without ean, the ones not found;
* ask for confirmation if it seems the two sets of data differ,
* add the cards to Abelujo's database.

Note: you must not have the ods file open at the same time.

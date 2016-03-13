Data sources and webscraping
============================

Where do we get the data of books and CDs from ?
------------------------------------------------

We get the detailed information about books and CDs from the following
websites:

- for french books:

  - we get them through decitre.fr

- for spanish books:

  - from casadellibro.com

- for german books:

  - from buchwagner.de

- CDs: from discogs.com.

Appart Discogs who provides a public api, we extract the data on the
other sites with some webscraping.

Why not use amazon's public apis ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Amazon is killing bookshops, little publishers, authors,
traductors and its employees. Screw Amazon.

On our results page, we add a link to the original website. We want to
support real bookshops that way.

How does web scraping work ?
----------------------------

Web sites are written using HTML, which means that each web page is a
structured document. Sometimes it would be great to obtain some data
from them and preserve the structure while we’re at it. Web sites
don’t always provide their data in comfortable formats such as ``csv``
or ``json``.

This is where web scraping comes in. Web scraping is the practice of
using a computer program to sift through a web page and gather the
data that you need in a format most useful to you while at the same
time preserving the structure of the data. (excerpt of xxx)

To scrap websites, we have to fire an HTTP request, get the response,
parse it and extract the interesting fields.

We have to construct an url that the website understands as a search
request. Observe the url:

    http://www.chapitre.com/CHAPITRE/fr/search/Default.aspx?cleanparam=&titre=&ne=&n=0&auteur=&peopleId=&quicksearch=noam+chomsky&editeur=&reference=&plng=&optSearch=BOOKS&beginDate=&endDate=&mot_cle=&prix=&themeId=&collection=&subquicksearch=&page=1

this one is pretty long but very interesting. In particular, we can
notice the "quicksearch" field, where our search terms are separated
by a ``+`` sign, as it must be with url parameters.

.. note::

   sometimes, the url is obfuscated. In that case, if the study of the
   POST parameters doesn't help, we'll need to use ``mechanize``.

The http connection is done with the `python-request
<http://docs.python-requests.org/en/latest/>`_ library. It is as
simple to use as::

   import requests
   response = requests.get(url)

then we can explore the response properties, like::

    response.status_code
    response.text

Parsing is done with `beautifulSoup4 <http://www.crummy.com/software/BeautifulSoup/bs4/doc/>`_.

.. note::

   Often, the page is partly rendered by javascript calls to the
   server. As a result, the html we get with `requests` from our
   python script isn't the same as the one displayed in the browser
   (when we see its source).

   A big tool to get the html after javascript execution is
   ``selenium``. However, we don't necessarity need it (and didn't so
   far). Indeed, we can study what calls make the page to what api
   endpoints and call them ourselves. Or simply get the html of a
   book's details page.

Often, we don't get all the data we want about a single book from the
list of results (we always want its price and isbn). We can get it
with a second pass, and scrape its details page.


.. seealso::

- http://docs.python-guide.org/en/latest/scenarios/scrape/
- http://scrapy.org/
- https://github.com/vinta/awesome-python#web-crawling
- `Portia, visual scraping <https://github.com/scrapinghub/portia>`_

Is it legal ?
~~~~~~~~~~~~~

No easy answer ! But it looks like it is.

How to add a data source
------------------------

Take example from `deDE/buchwagner/buchWagnerScraper.de <https://gitlab.com/vindarel/abelujo/tree/master/search/datasources/deDE>`_.

See also the `BaseScraper`.

But first, contact us !

Test strategy
-------------

Unit tests and end-to-end tests.

They can be long when we run them, because we are awaiting HTTP
requests. We do not use a cache to run end to end tests.


To run end to end tests ("live tests"), go to the `datasources` directory and run::

    make testscrapers

These tests are defined for each scraper. They use a base class in
``utils/baseScraper.py``. The expected results are defined in their
``test_scraper.yaml``. This yaml defines a list of books we are
expecting to find in the scraping results. The base tests fires a
search, filters the results (with the title, the ean and the price
which are expecting to be the same) and then it tests more fields
(publishers, authors, etc). It also tests that the ``postSearch``
method returns what is expected.

TODO: run tests periodically.


Cache policy
------------

We use ``requests_cache`` to automatically cache the http requests.

TODO: give an option to bypass it.


Known bugs
----------

See `the list on gitlab <https://gitlab.com/vindarel/abelujo/issues?assignee_id=&author_id=&label_name=datasource&milestone_id=&scope=all&sort=created_desc&state=opened>`_.


Future
------

Integrate pages that need javascript with Selenium. It's easy, it just
needs more processing, so let's try to avoid it first. (ask us, we're
doing it for Foyles.com.uk)

For sites of which the url is not guessable, use ``mechanize``.

Study how ``xpath`` can help shorten the code and scrapers creation.

Make a library of its own so that in can be used in other projects.

Test with continuous integration on GitlabCI.

How to import an ods LibreOffice sheet
--------------------------------------

It's on the command line only and is still a work in progress.

The ods (or csv) file can be of two forms:

- it has a row containing the name of the columns. In that case, it
  must have a "title" column or a "isbn" one.

- it contains only data, it has no row to declare the column names. In
  that case, we use a settings.py file to declare them.


In short::

    make odsimport odsfile=myfile.ods

This functionnality relies on 2 scripts:

* `search/datasources/odslookup/odslookup.py` is responsible for
  extracting the data from your ods and fetching the data for each
  row. It returns a big list of dictionnaries with, supposedly, all
  the information we need to register a Card to the database. When it
  fetches results it must check if they are accurate. Beware the false
  positives !

* `scripts/odsimport.py` calls the script above and adds everything in
  the database. It adds the cards with their quantity, and creates
  places, editors and distributors if needed.

There's more info in them if you want to develop (and want to cache
http requests or store and retrieve a set of results).

The ods file needs at least the following information with the
corresponding english or french label (case is not important):

* the card's title ("title", "titre"),
* the publisher ("éditeur"),
* the distributor (will be the publisher by default),
* its discount ("remise"),
* the public price (first column with "price" or "prix" in it) ,
* the quantity ("stock", "quantité").

There's a little test suite::

    cd search/datasources/odslookup
    make test

 Upcoming infos: the category and historical information.

.. Note:: Known limitations:

          * the script will include a few false positive results.  It
            can not make the difference between "a title t.1" and "a
            title t.2".

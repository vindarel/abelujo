Data sources and webscraping
============================

Where do we get the data of books and CDs from ?
------------------------------------------------

We get the detailed information about books and CDs from the following
websites:

- for french books:

  - we get them through chapitre.com

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
time preserving the structure of the data. (excerpt of

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

   if the page is rendered with javascript, we'll use ``selenium``.


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

But first, contact us !

Test strategy
-------------

Unit tests and end-to-end tests.

They are long the first time we run them (awaiting HTTP requests),
quick the second time (using the cache).

TODO: finish e2e tests

TODO: Continuous integration.

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

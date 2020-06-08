Changelog starting from v0.5 (2018/09/18)

## 2020-06, 2020-05

### New features

- searching My Stock now correctly ignores accents: searching
  "stromquist" also returns "strömquist".
- My Stock: we can filter results by date of creation of the card in
  our database. We choose an operator like "<=" and we write a date
  indicator, like: "june, 2020", "1st may 2016", etc. For details: see the
  `dateparser` library, and the online documentation.
- we get more fields from Dilicom: the distributor GLN and the theme.
- My Stock: we don't run a DB query to get the newest books at the
  landing page anymore, we show nothing. The page loads quicker.

Some **clients** features:

- create clients
- at the Sell point: choose a client and edit a bill, in PDF. Create a
  client on the fly with the "+" button.

more to come for clients.


### Admin

New admin scripts (all to be run with `./manage.py <script>`):

- `gen_ascii_fields`: command to run in order for the search to work
  regardless of accents. This creates new database fields, the title
  and authors names in ascii, without accentuated letters, which are
  also used during the search.
- `import_dists`: import all known distributors of Dilicom, via our
  CSV export of Dilicom data. The FEL à la demande only gives the
  distributor GLN, we must get the name ourselves, hence the need of
  an external CSV file.
- `update_all_with_dilicom`: update ALL the cards with Dilicom
  data. Update the publisher (to have one unique name across the
  application), the theme, the distributor GLN, and all.
- `remove_unused_publishers`, useful after the above script.
- `list_publishers` and do nothing.

## Upgrade instructions

As usual (make update).

Run the `gen_ascii_fields` script.

If you use Dilicom, you'll certainly want to run a couple of scripts above.


## 2020-01…04

### New features

- we handle a Swiss books datasource.
- hence, we handle different currencies (euro "10€", swiss franc "CHF 10")
- in baskets: new action "add to shelf…" that empties the basket so
  than we can do it again for another shelf. Useful when receiving
  books.
- TODO

## 2019-XX

TODO


## 2019-02

### Fixes and enhancements

- the Commands view was too slow and the pages were changed.
  * we now have an index listing all the suppliers that have some cards to command, and each has its own Command page.
  * the bottleneck function at the problem origin (computing the total
    quantity of a given card in all places), also impacting other
    pages, was dramatically improved (from minutes to 5 seconds).

## 2018-12

### New Features

Return a list to its supplier.

- in a list, we can choose the action "return to supplier…":
  - every book is removed from the stock with the corresponding quantity
  - it creates an "Out Movement", for history
  - we can see the movement in a card's history


## 2018-11

### New Features

- Import a csv file with an ISBN and a quantity with a manage.py
command. See developer documentation.


# v0.6 2018-11-16

### Fixes

- pinned more dependencies (whitenoise)


# v0.5

## 2018-10

### New Features

Deposits rewrite:

- the Deposits section was re-written.


## 2018-09

### New features

- a list/basket can be linked to a supplier, so than further actions
  (apply to the stock, receive a parcel,…) can set this supplier for
  all the cards.

Changelog starting from v0.5 (2018/09/18)

## 2020-06

### New features

- searching My Stock now correctly ignores accents: searching
  "stromquist" also returns "strömquist".
- My Stock: we can filter results by date of creation of the card in
  our database. We choose an operator like "<=" and we write a date
  indicator, like: "june, 2020", "1st may 2016", etc. For details: see the
  `dateparser` library, and the online documentation.

### Upgrade instructions

- run `python manage.py gen_ascii_fields`.

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

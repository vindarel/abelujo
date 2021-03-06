Changelog starting from v0.5 (2018/09/18)

## v0.13 (2020-07, 2020-06, 2020-05)

### New features

New **bibliographic and stock** features:

- **searching the stock** now correctly ignores accents: searching
  "stromquist" also returns "strömquist".
- My Stock: we can **filter results by date of creation** of the card in
  our database. We choose an operator like "<=" and we write a date
  indicator, like: "june, 2020", "1st may 2016", etc. For details: see the
  `dateparser` library, and the online documentation.
- we get more fields from Dilicom: the **distributor GLN and the theme**.
- My Stock: we can select books and assign them to another shelf.
- on a card page, we can **change the shelf quickly** (a select field is present).

New **sell** features:

- new "coupon" payment method. The sell appears in the history but is
  not counted in the day's revenue. Indeed, the coupon was sold before
  and we must not count the sell twice. More about coupons and sell
  options are coming.
- new possibility to return a book during the sell, by inputting "-1" in the quantity field.
- if an ISBN is scanned but not found (in the stock or on Dilicom), warn the user with a yellow message, and allow to scan other books.

New **clients** features:

- create clients
- during a sell: choose a client or create one on the fly with the "+" button.
  - generate a bill of this sell for this client, in PDF.
  - on validation, the client is registered for this sell. On the
    history, we view the clients.

New **deposits** features:

- added: we display a missing message to the user when a deposit of that name already exists.
- added a "create" button on a deposit page.
- changed: when creating a new deposit the distributor is now optional
- changed: go to the deposit's page after creation success, not the list of deposits.


### Other enhancements

- The admin page for shelves shows how many books each shelf contains.
- we can now easily configure payment methods in a configuration
  file. See the developper documentation, "installation" page.
- creating a command (with the OK button) was dramatically sped up
  (from a few seconds to a fraction of a second).
- selling a card that is in a deposit automatically sells it from the
  deposit. Previously, we had to be explicit in the sell UI.
- the default timezone was set to Paris (UTC+1/+2), preventing some
  date inconsistencies.

**Speed ups**:

- faster loading My Stock page: we don't display the newest books at the
  landing page anymore.
- searching cards by keywords is nearly 2 times faster.


### Admin

New admin scripts (all to be run with `./manage.py <script>`):

- `gen_ascii_fields`: command to run in order for the search to work
  regardless of accents. This creates new database fields, the title
  and authors names in ascii, without accentuated letters, which are
  also used during the search.
- `update_all_with_dilicom`: update ALL the cards with Dilicom
  data. Update the publisher (to have one unique name across the
  application), the theme, the distributor GLN, and all.
- `import_csv_with_dilicom`: batch-import a CSV (ISBN;quantity) with
  Dilicom.
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

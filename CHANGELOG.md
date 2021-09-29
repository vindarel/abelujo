Changelog starting from v0.5 (2018/09/18)

## DEV

### New features

- support for **Stripe payments**, sent from a front website.
  - with validation emails (to the client and the show owner)
  - shipping costs
  - books bought online create **reservation objects** on Abelujo side, then the show owner validates the sell (or not).
- **user permissions**: non-staff members can only see the stock. They can:
 - see the stock
 - search for books
 - see a books' page
 - see the history
 - see client reservations
 - see special pages (bookshop selection for website)
 - => Create a new user from the admin panel, don't give it any rights.

### Other enhancements

- **Sell: import a client's reservations** (the ones we received, but import all of them anyways if needed).
- **Sell: show the total price in red**.
- searching our **stock**: more sort order options (sort by creation date of the book, by title (anti) alphabetically, by price, by shelf, by publisher.

### Admin

- new script: `manage.py export_stock --format csv` to create a csv file from all cards in stock and with a quantity > 0. Because doing that from the UI can be too long.


## v0.18 (2020-12, 2021-09)

yes it's a +3 version jump because we are late and have 3 big new features!

### New features

- new **Reception menu**: receive books, scan them in a row and register them quickly in the appropriate shelf (if they don't have one already).
- new **Client commands**: register commands for clients from the book view or from the search view. See them all, send an email to the client.
  - if the book is not in stock, show it in the command list.
- Abelujo now supports the **Electre API** as an alternative to Dilicom's FEL à la demande (the FEL Onix complet is being worked on).
- new special page to list books to *not* show on the frontend website (exclude them from the API). This feature must be enabled, see in admin.
- **Sell**: support to **print sell receipts** with the USB thermic receipt printer [Epson TM-20](https://www.amazon.fr/gp/product/B07Y59V9LP/ref=as_li_tl?ie=UTF8&camp=1642&creative=6746&creativeASIN=B07Y59V9LP&linkCode=as2&tag=abelujo-21&linkId=b3938b7d12f66b76d2d9e1c5d6f6e8b7). Previously, you could print a bill. The process is now must faster.
  - install the printer
  - print a test page
  - before validating a new sell, ask your browser to print the current page and choose the ticket printer.

- Baskets: added an action to add all the cards to the stock, without having to choose a shelf. This greatly **speeds up the registration of new books**.
- We added a global parameter to **use CLIL themes for the shelf** name,
  in order to speed up the registration of new books (this removes the
  only required manual step until now). We can use the new action
  above, and still have shelves for our books.
- History: added a button to quickly **command** a book (add it into the command list).
- History: the history gets more **breakdown**: it shows totals for each type of product (book, CD, beverage…)
- History: the history page of the month and the day show the **best sells** for each kind of product: books, but not only.
- Sell page: we can pay with **two payment methods**.
- Sell page: print adapted to print **receipts** (tested with Epson TM-20)
- the Commands page shows **all cards to command**, in addition to them grouped by supplier. This makes it easier to download a CSV and send it to a supplier.
- added a button to collapse the left menu. We can now work in "full screen". Especially useful for the Raspberry Pis and views with a lot of information (Reception, lists…).
- We can choose what books to show on the ABStock catalogue from within Abelujo (see new page `/catalogue-selection`).
- We can now see the past inventories.
- quick search bar: we introduce a way to filter our search. Type "keyword ed:foo" (`ed:foo` is important here) to filter the results by publisher containing "foo" in its name.

More data delivered with the API:

- say if a book was found on Dilicom or not (`dilicom_unknown_ean`), on `/api/card/:id?with_dilicom_update=1`.

### Other enhancements

- **Bills** enhancements (added a unique number, better TVA details, other fixes).
- on a card page, the cart button to add a card to the command list was fixed to add 1 copy at each click (instead of adding the book, but not updating the quantity to command).
  - in addition, the button also shows the quantity in the command list.
- new **Preference setting**: choose wether or not to automatically add a card to the list of commands after a sell (if its quantity in stock gets lower its minimal treshold).
  - **changed**: this features is now disabled by default.
- when we have more than one places in the database, allow to choose where we sell books from in the **sell page** (this was removed seven months ago, it is back but hidden by default).
- during a sell, we warn the user if a price of a book that is being sold was updated (it can be updated asynchronously, just after it was added to the sell).
- we do not emphasize about many (selling) places anymore. It adds too much complexity and was seldom used. Now Abelujo expects one stocking place and one selling place.
  - you can still create other (selling) places, it mostly works, but some details are lacking. You might get some confusion (but no data loss).
- fixed the broken redirection after a logout and new login.
- **speed up** improvements for the history display (more than 10x).
- **speed up** improvements to the CSV and TXT download of history logs (30%).
- deposits: we don't mention anymore the type of deposits that are sent by us to the exterior world.
- **speed up** to display the list of commands.
- **speed up** of the analysis of inventories (x10, but not always at the first access).
- **speed up** of the inventory analysis page.

### For administrators

- **ease of installation**: the installation requires many fewer steps and dependencies, see below.
- new feature flag: `FEATURE_EXCLUDE_FOR_WEBSITE` (defaults to False): exclude books from the API to not show them on the frontend website.
- new feature flag: `FEATURE_ELECTRE_API` (False), as well as the related password and username settings.
- new feature flag: `FEATURE_SHOW_RESERVATION_BUTTON`, defaults to `True`: show a reservation button on the card page (reserve for a client).
- new script: `./manage.py move_from_place --origin <id>` to move all cards from one place to another (the destination defaults to the default place). It might be useful, because Abelujo doesn't encourage to use more than one selling place anymore.
- new script: `./manage.py get_higher_covers`: replace book covers (gotten from librairie-de-paris) to higher resolution ones. To run once.

### Upgrade instructions

- Abelujo doesn't need npm or Node packages any more for its installation, making the installation and updates much easier.
- Nothing special, but it is recommend to run the `update_all_with_dilicom` script.
- see the preferences page and check "auto_command_after_sell" to get the old behaviour.
- optional: clean up cards' types with `fix_types` (set their type correctly to "book" if they have a book ISBN).

## v0.13.3 (2020-09, 2020-11)

### New features

- new **boxes** menu. It's like the lists, except that adding a book in a "box" removes it from our stock. This is particularly useful when working with commands. We take a book from the shelf, put it in the parcel, and the quantity in stock reflects the reality. Before, we had to validate the list.
- in the **history**: we now differentiate the revenue from books and other products, that have a different VAT. Necessary for accounting.
- we can **generate a bill for a list** and **generate a bill during a sell**.
  If the client has a default discount, apply it.
- we can **sell a list**.

### Enhancements

- adding a book in a **list** always moves it at the top of the list. Before, there were cases where an existing book would not move, so we could not see its new quantity easily.
- lists: sort books by last modified date. This allows to see the last books we added to a list.
- we added a button on the card page to quickly **add this book to the command list**. Previously, books were added to the command list when they were sold and their quantity got below a given treshold. There was no manual way, this is now fixed.
- **automatic commands**: when a book is added to the list of books to command, its quantity to command is not set to 1 (or more) anymore, but 0. That way, the booksellers will /select/ what books to command and how much, instead of /un-selecting/ them.

### Fixes

- baskets: there was an issue in the rendered HTML that prevented from sorting the table by title and publisher. It is now fixed.


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

Coding style
============

We have to decide on some rules to make the code coherent. In
particular, naming conventions, code organization and (the heart of
it) some implementation details.


Naming conventions
------------------

Pluralize class and method names dumbly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Example: we have a class named `Shelf`. In english, its plurial is
`shelves`. But it makes it a bit more difficult to search-and-replace
and to be coherent in the API. Let's see how chocking it is to
pluralize it wrongly, with an s in the end: `shelfs`.

Quantity, qty, number, count ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prefer `qty`.

API
---

Don't use Django's serializer.

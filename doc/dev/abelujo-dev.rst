Abelujo development
===================

Tests coverage
--------------

We simply use coverage (django\_coverage is buggy).

Run with::

    make cov
    # or:
    # coverage run --source='.' manage.py test search
    # coverage html  # and open: firefox htmlcov/index.html

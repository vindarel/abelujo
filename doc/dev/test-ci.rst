Continuous Integration
======================

We use gitlab CI. See `.gitlab-ci.yml`.


Testing strategy
----------------

We have different sorts of tests to write and run: unit tests, end to
end tests, tests of the user interface and integration tests.

Like with all python software, we write **unit tests**. They are aimed at
testing logical blocks of code, like a function on its own. We use the
`unittest` module and the Django facilities for the backend.

We must also unit test the javascript code (the logic lies in
angularjs controllers and directives).

Writing tests is mandatory to check that our code doesn't break with
time and refactorings. They are also necessary to reproduce and fix
bugs, and they are useful, when we write them, to better understand
and design the code we want to write. That's part of why a developper
should embrace the `Test Driven Development` (TDD) workflow: the goal
is to write tests before even writing the firt line of code.

Testing that a method does the expected logic doesn't guarantee that
it works with data from the real world. For example, let's consider
our web scrapers that pull data from online bookstores. We have to
write unit tests to check that they work as expected, but we also need
to test that they still work against the current website on the
internet. Indeed, remote websites can change, the format of the data
they accept or return can change and break our code. We then have to
run tests against the real world once in a while. We call those **end
to end tests**.

We also write a lot of javascript for **the user interface** in the
browser. Some pages do a lot of logic with javascript. The selling
page, for example: it asks for data to the server, it does some
calculation and it gives some data back to the server to be registered
in the database. We need to test all that too. This is doable with the
`testcafe <https://devexpress.github.io/testcafe/>`_ test framework.

Now we know how to test each part of our application. Great, but this
isn't enough. Nothing guarantees that those parts work happily
together ! We then need **integration tests**. They are fortunately
done partly with **testcafe** (because it launches a real web browser
with the current state of the application we can test the interaction
with the server).

But we also have to test that all the packages and software that we
rely on install correctly. We do it partially with `tox
<https://testrun.org/tox/>`_, which tests the python side, that our
`pip` dependencies install correctly in a fresh environment, and that
no one is missing ;) At is core it is made to test the installation
against multiple versions of python but we don't need that (yet).


Running Tests
-------------

To run python unit tests::

    make unit # or ./manage.py test search.tests.testfile.someClass.some_method

To run the javascript unit tests::

    TODO !

To run the javascript end-to-end tests, open 2
terminal windows:

- run our web app with the usual `make run` (or `./manage.py runserver`)
- run the tests: `make testcafe`.

.. note::

   Some tests rely on the testing data that we load with `make data`.

   You need at least nodejs v4 (so not Debian's default). See
   https://github.com/nodesource/distributions#installation-instructions
   and the Node Version Manager: https://github.com/creationix/nvm


Tests coverage
--------------

We simply use coverage (django\_coverage is buggy).

Run with::

    make cov
    # or:
    # coverage run --source='.' manage.py test search
    # coverage html  # and open: firefox htmlcov/index.html

Testing the installation script on Docker
-----------------------------------------

See `docker/dockentry.sh` and `docker/install.sh`.

The first one creates a sudo user and runs the second one.

Given you have Docker already installed, run the installation script
in a fresh Ubuntu 16:04 with::

  chmod +x dockentry.sh
  docker run  -v "$(pwd)/docker":/home/docker/ -ti ubuntu:16.04 /home/docker/dockentry.sh


`-v` mounts the files in the current directory into docker's home
(user `docker`). `-i` is for interactive section. The final argument
runs the given script (to create the sudo user etc).

You can also step into the image with simply `-ti ubuntu:16.04`, and
run bits of scripts manually from there.

Testing the sending of emails
-----------------------------

See ``make send_test_emails``. It will call a unit test, create fake data and construct an email object **and send it**, to your testing address configured in conf.py.

See the URL http://localhost:8000/en/private/test/mailer/owner-confirmation.html to see how an email is rendered.

To test Stripe hook validation, install the Stripe CLI tool and run::

    stripe trigger payment_intent.succeeded

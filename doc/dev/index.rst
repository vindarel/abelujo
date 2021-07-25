Welcome to Abelujo's developer documentation
============================================

Contents:

.. toctree::
   :maxdepth: 2

   installation.rst
   dilicom.rst
   use-manage.rst
   angular-crash-course
   webscraping.rst
   django-dev.rst
   api-dev.rst
   clientside-dev.rst
   test-ci.rst
   codingstyle.rst

How to contribute to Abelujo (git, gitlab, workflow)
----------------------------------------------------

To help develop Abelujo (welcome !) you need some basics in Python and
Git. Then you'll have to find your way in Django. You can help with
html, css and javascript too. And if you're experienced with
Docker, you'll have some work !

- Python crash course: http://learnpythonthehardway.org/book/
- Django documentation: https://docs.djangoproject.com/en/1.6/
- Python ecosystem: https://github.com/vinta/awesome-python

We use ``git`` as a source control system. You'll need to learn the
basics (essentially what ``git commit``, ``git pull``, ``git push``
and ``git branch`` do). To understand how creating branches help with
our workflow, see `the Github Flow
<https://guides.github.com/introduction/flow/index.html>`_ (just
replace Github by Gitlab).

- best Git ressource: http://www.git-scm.com/
- check out those git GUI too: http://www.git-scm.com/downloads/guis and `emacs' magit interface <https://magit.github.io/master/magit.html>`_.

Allright ! Take your time, I'll wait for you. The next step is easier,
you're going to **create an account on Gitlab.com**. Gitlab is a
web-based Git repository manager. It also has an issue tracking system
and a basic wiki. It's like Github, but there's an open-source
version of it. The sources of Abejulo are hosted on `Gitlab.com
<https://gitlab.com>`_ . So, go there and create an account. You don't
need one to grab the sources, but you need one to cooperate with us.

Indeed, the workflow is as follows:
- you have your copy of Abelujo, forked from the original,
- you work on your repository.
- you regularly update your repository with the modifications of the
  original repository (you want to be up to date to avoid conflicts).
- when you're finished, you open a merge-request on Gitlab.
- we discuss it, it is eventually merged.

Once you have an account, you need to fork Abelujo's repository. With
your fork, you'll be able to (easily) suggest to us your new
developments (through merge-requests). So, go on `Abelujo's repository
<https://gitlab.com/vindarel/abelujo>`_ and click your "fork" button.

Now you can pull the sources of **yours** Abelujo copy::

    git clone git@gitlab.com:<your_user_name>/abelujo.git

Choose the ssh version of the link over the https one. With some
configuration of ssh on your side, you won't have to type your
username and password every time.

.. Note::

    If we recall well (ping us if needed), you need to add your ssh
    public key to your gitlab account (profile settings -> ssh
    keys). This key is located at "~/.ssh/id_rsa.pub". If it doesn't
    exist, create it with "ssh-keygen rsa". A passphrase isn't
    compulsory.

You're ready to work on your local copy of Abelujo. You can commit
changes and push them to your gitlab repository. Hey, we are also
working on it at the same time, so don't forget to *pull* the changes
once in a while, and to work in a branch distinct from master, this
will be easier.

And when you want to suggest changes to the official repository, you
press the button "Pull Request". We'll have a place to tchat about
your changes, and when a maintainer feels like it's ok, he or she will
merge your changes. We can also give you the right to do so.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

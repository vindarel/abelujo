Git configuration
=================

We work with a `git submodule`:
https://www.git-scm.com/book/en/v2/Git-Tools-Submodules.

If you develop on the submodule side, a ``git diff`` on the project
root will only say that the submodule has local modifications (is
dirty), but won't tell you what changed. Set this setting::

    git config --local diff.submodule log

Now a git diff will show the submodule's log.

.. note::

   That helps in Emacs' Magit too.


Editors configurations
======================


Here we share tips on our favorite(s) editors. Indeed, it must assist
you in many areas: development in python and javascript (syntax
highlighting, code checker, ...), development with AngularJS,
documentation writing, json editing, project management, and why not
as a test runner and a shell.


Emacs
-----

Emacs' package manager
~~~~~~~~~~~~~~~~~~~~~~

Starting with version 24 Emacs has an official package manager:
`package.el` (we already had el-get and it still works). But you won't
go far if you don't activate the MELPA repository: see
http://wikemacs.org/wiki/MELPA

Now to install a package::

  Alt-x package-install RET the package RET

.. note::

   The packages below are available either on MELPA or on the
   official package.el repository (GNU ELPA).

Not sure ? Use a starter kit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

True enough, Emacs isn't user friendly without some configarution. If
you didn't tweak it a lot yet, it's a good idea to start with an
excellent configuration out of the box. There are some options and our
favorite is `Prelude <https://github.com/bbatsov/prelude>`_.

Vim emulation
~~~~~~~~~~~~~

You can get modal editing with the excellent `evil-mode`: http://wikemacs.org/index.php/Evil

Python
~~~~~~

See http://wikemacs.org/wiki/Python


Javascript
~~~~~~~~~~

See: http://wikemacs.org/wiki/JavaScript

- js2-mode: http://wikemacs.org/wiki/Js2-mode

LiveScript
~~~~~~~~~~~

- A basic but decent `livescript-mode`:
  https://github.com/bdowning/livescript-mode (this is not the one in
  MELPA) It deals correctly with indentation.


Django mode
~~~~~~~~~~~

https://github.com/myfreeweb/django-mode

Gives a menu and some global functions to interact with Django.

Angular snippets and utilities:


- syntax highlighting of angular keywords in html templates, snippets and tab completion: https://omouse.github.io/angularjs-mode/

- syntax highlighting in `jade` templates: our `angularjs-jade-mode`: https://gitlab.com/snippets/4113
- our `angular-utils`: https://gitlab.com/emacs-stuff/my-elisp/blob/master/angular-utils.el may offer useful commands, may not.

Jade templates
~~~~~~~~~~~~~~

- `jade-mode` for syntax highlighting
- our `html2jade` to copy-paste html snippets and turn them to jade:
  https://gitlab.com/emacs-stuff/html2jade

JSON
~~~~

- Check the json integrity with `flymake-json
  <http://melpa.org/#/flymake-json>`_. You need::

    npm install -g jsonlint

- `json-mode`: syntax highlighting and commands to reformat.

Shell interaction
~~~~~~~~~~~~~~~~~

See http://wikemacs.org/wiki/shell

Translating po files
~~~~~~~~~~~~~~~~~~~~

See the
[po-mode](https://raw.githubusercontent.com/andialbrecht/emacs-config/master/vendor/po-mode.el)
and [its
documentation](https://www.gnu.org/software/gettext/manual/html_node/Installation.html). When
activated, press `u` to go to the next unread entry and type Enter to edit it.


See also
~~~~~~~~

- effectively open files and run commands on the project with
  `projectile <https://github.com/bbatsov/projectile>`_.
- `elscreen <http://wikemacs.org/wiki/Elscreen>`_ to have tabs.

More documentation
~~~~~~~~~~~~~~~~~~

- `awesome-emacs`: https://github.com/emacs-tw/awesome-emacs
- wikemacs

Shell
-----

npm completion
~~~~~~~~~~~~~~

Run::

    .< (npm completion

on your current shell and put this command in your .bashrc.

If available on your system, the following does the same::

  apt-get install npm-completion

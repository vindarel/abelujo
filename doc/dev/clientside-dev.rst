Client-side development
=======================

Write custom CSS
----------------

To customize the look of Abelujo, you can set your CSS rules in each
app ``<name of the app>/static/<name of the app>/style.css`` file,
i.e. in ``search/static/search/style.css``. This file will be loaded
automatically by Django, and collected when we run `collectstatic`
command.


Write JavaScript in Livescript
------------------------------

.. note::

   We used LiveScript but we're now switching to Vue.js with plain Javascript. https://vuejs.org

Our current Angularjs controllers are written in Livescript::

    * http://livescript.net

The LiveScript executable and repl is `lsc`.

Now to compile LiveScript files run `make gulp`.


You can recompile everything on every change with::

    gulp watch

.. note::

   If you have the same file with both a js and a ls extension, the
   javascript will take precedence (it is appended first in
   ``abelujo.js`` so it is read first by angularjs).

Html and CSS to improve the user interfacet
------------------------------------------

How to improve the user interface with html and CSS ?

Html with Jade templates
~~~~~~~~~~~~~~~~~~~~~~~~

Note that we don't write pure html, we use the jade templating
language instead, which compiles to html.

- http://jade-lang.com/

Very quick reference:

.. code-block:: html

   <div class="nav", id="default-id", href="#">
      <ul> etc

is written

.. code-block:: jade

   div.nav#default-id(href="#")
      ul etc
   // and the div can be omitted:
   .nav#default-id(href="#")
      ul etc

Le't consider possible pitfalls:

If you comment out a node, its children will be commented out as well

.. code-block:: text

  // div.commented
       span.commented-by-its-parent

Bootstrap and custom CSS
~~~~~~~~~~~~~~~~~~~~~~~~

The css file for the app is at `search/static/search/style.css`.

Our CSS layout and widgets come from Bootstrap3 and Angular-UI:

- http://getbootstrap.com/components/
- https://angular-ui.github.io/bootstrap/versioned-docs/0.14.3/ .


Add a bower dependency
----------------------

If we want to use a new javascript library for development on the
client side, we have to make the html page load it. We use `bower` for
that. It is a quick process:

1. add the library name and its version to the `bower.json` in the
   `dependencies` list.

   warning:: be sure to check the json format. Use your editor's tool
   for that.

2. install it::

     bower install

   The sources are now at `static/bower_components/`.

3. add the path to the library's minified js to the `gulpfile.js`, in
   the `vendorJsFiles` list. It is generally situated at
   `static/bower_components/mylib/mylib.min.js` but it can vary.

4. build the javascript files::

     gulp

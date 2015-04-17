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

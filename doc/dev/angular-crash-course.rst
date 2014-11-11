Angular crash course
====================

Add Angular to a web (Django) project
-------------------------------------

Reference the sources
~~~~~~~~~~~~~~~~~~~~~

Basically, as for any web project, we need to link the javascript
sources to a html file. We do that in the ``head`` like this.

.. code-block:: html

    html
      head
        script(src="http://ajax.googleapis.com/ajax/libs/jquery/1.9.0/jquery.js", type="text/javascript")
        script(type='text/javascript', src="js/build/abelujo.js")


That way, we take the jquery sources from the servers of google, and
we look for our own ``abelujo.js`` sources in our filesystem.

But where are those sources located ? In our Django settings we defined
the ``STATIC_ROOT`` variable. Now we'll reference to it with the ``{% static %}`` tag:

.. code-block:: html

    html
      head
        script(type='text/javascript', src="{% static 'js/build/abelujo.js' %}")




Include Angular in the template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See this simple example: https://angularjs.org#add-some-control

Given that we wrote correctly a minimal Angular function and a
controller for startup, we can call Angular:

.. code-block:: html

     html(ng-app="abelujo")

And we need to call a controller where we want Angular to take action, like:

.. code-block:: html

    div(ng-controller="IndexController")
      input(type="text", ng-model="yourName", placeholder="Enter a name here")
      div Hello {% verbatim %} {{yourName}} {% endverbatim %} !


Build the js sources
--------------------

``Gulp``, as introduced in the tool choices section, is responsible for
concatenating every js and css files into a single one, ``abelujo.js``
(among other actions).

When you modify the js, re-build with gulp::

    gulp

see the gulpfile for the other actions.


What happens and when ?
-----------------------

When we access our root html page:

* Django reads ``base.html`` and loads the "normal" html. If our
  template wants to display an Angular variable enclosed in double
  brackets, we will see them, since Angular didn't interpret them yet
  (unless we use the appropriate directive).
* the scripts called in the ``head`` are loaded: the css and the
  javascript libraries. Angular loads up. Our custom js loads too.
* Angular parses the DOM (Document Object Model, i.e. the html tree)
  and sees a call to ``ng-app="abelujo"``. Angular starts and looks
  for a module called "abelujo". Fortunately, our js code provides
  one, so it is called.
* Angular evaluates the other directives included in the DOM and
  executes the logic of the controllers, like our "IndexController".

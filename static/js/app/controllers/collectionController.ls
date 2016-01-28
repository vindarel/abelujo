angular.module "abelujo.controllers", [] .controller 'collectionController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', ($http, $scope, $timeout, utils, $filter, $window) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines} = require 'prelude-ls'

    $scope.query = ""
    $scope.cards = []
    $scope.places = []
    $scope.place = null
    $scope.categories = []
    $scope.category = null
    $scope.publisher = null

    $scope.selectAll = true
    $scope.selected = {}

    $scope.card_types =
          # WARNING duplication from dbfixture.json
          {name: gettext("all publication"), id:null}
          {name: gettext("book"), group: gettext("book"), id:1}
          {name: gettext("booklet"), group: gettext("book"),id:2}
          {name: gettext("periodical"), group: gettext("book"), id:3}
          {name: gettext("other print"), group: gettext("book"), id:4}
          {name: gettext("CD"), group: gettext("CD"), id:5}
          {name: gettext("DVD"), group: gettext("CD"), id:6}
          {name: gettext("vinyl"), group: gettext("CD"), id:8}
          {name: gettext("others"), group: gettext("others"), id:9}


    $http.get "/api/places"
    .then (response) !->
        $scope.places = response.data

    $http.get "/api/categories"
    .then (response) !->
        $scope.categories = response.data

    $http.get "/api/publishers"
    .then (response) !->
        $scope.publishers = response.data

    # Get cards in stock
    $http.get "/api/cards"
    .then (response) !->
        $scope.cards = response.data
        for elt in $scope.cards
            $scope.selected[elt.id] = false

    $scope.validate = !->
        params = do
            query: $scope.query

        if $scope.publisher
            params['publisher'] = $scope.publisher.pk
        if $scope.place
            params['place'] = $scope.place.id
        if $scope.card_type
            params['card_type'] = $scope.card_type
        if $scope.category
            params['category'] = $scope.category.pk

        $http.get "/api/cards", do
            params: params
        .then (response) !->
            $scope.cards = response.data

    # Add a checkbox column to select rows.
    $scope.toggleAll = !->
        for elt in $scope.cards
                $scope.selected[elt.id] = $scope.selectAll

        $scope.selectAll = not $scope.selectAll
    # Set focus:
    angular.element('#default-input').trigger('focus')

    $window.document.title = "Abelujo - " + gettext("Stock")

]

# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

angular.module "abelujo.controllers", [] .controller 'collectionController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', '$cookies', '$uibModal', '$log', 'hotkeys', ($http, $scope, $timeout, utils, $filter, $window, $cookies, $uibModal, $log, hotkeys) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {Obj, join, sum, map, filter, lines} = require 'prelude-ls'

    $scope.language = utils.url_language($window.location.pathname)

    $scope.query = ""
    $scope.cards = []
    $scope.places = []
    $scope.place = null
    $scope.shelfs = []
    $scope.shelf = null
    $scope.publisher = null
    $scope.distributors = []
    $scope.distributor = null
    $scope.baskets = []
    $scope.show_images = true

    $scope.quantity_choice = null
    $scope.quantity_choices = [
      {name: gettext(" "), id: ""}
      {name: "< 0", id: "<0"}
      {name: "<= 0", id: "<=0"}
      {name: "0", id: "0"}
      {name: "> 0", id: ">0"}
      {name: "> 1", id: ">1"}
      {name: "> 2", id: ">2"}
      {name: "> 3", id: ">3"}
      {name: gettext("between 1 and 3"), id: "[1,3]"}
      {name: gettext("between 1 and 5"), id: "[1,5]"}
      {name: gettext("between 3 and 5"), id: "[3,5]"}
      {name: gettext("between 5 and 10"), id: "[5,10]"}
      {name: gettext("> 10"), id: ">10"}
    ]
    $scope.price_choice = null
    $scope.price_choices = []

    $scope.define_price_choices = !->
        $scope.price_choices = [
          {name: gettext(" "), id: ""}
          {name: "0", id: "0"}
          {name: "<= 3 #{$scope.meta.currency}", id: "<=3"}
          {name: "<= 5 #{$scope.meta.currency}", id: "<=5"}
          {name: "<= 10 #{$scope.meta.currency}", id: "<=10"}
          {name: "<= 20 #{$scope.meta.currency}", id: "<=20"}
          {name: gettext("between 0 and 5 #{$scope.meta.currency}"), id: "[0,5]"}
          {name: gettext("between 0 and 10 #{$scope.meta.currency}"), id: "[0,10]"}
          {name: gettext("between 5 and 10 #{$scope.meta.currency}"), id: "[5,10]"}
          {name: gettext("> 5 #{$scope.meta.currency}"), id: ">5"}
          {name: gettext("> 10 #{$scope.meta.currency}"), id: ">10"}
          {name: gettext("> 20 #{$scope.meta.currency}"), id: ">20"}
        ]

    $scope.date_created = null
    $scope.date_created_sort = ""
    $scope.date_created_sort_choices = [
      {name: " ", id: "" }
      {name: "<=", id: "<=" }
      {name: "=", id: "=" }
      {name: ">=", id: ">=" }
    ]

    # pagination
    $scope.page = 1
    $scope.page_size = 25
    $scope.page_sizes = [25, 50, 100, 200]
    $scope.page_max = 1

    # Read variables from local storage.
    show_images = $window.localStorage.getItem "show_images"
    if show_images != null
        if show_images == "true"
            show_images = true
        else
            show_images = false
        $scope.show_images = show_images

    page_size = $window.localStorage.getItem "page_size"
    if page_size != null
        $scope.page_size = parseInt(page_size)

    $scope.selectAll = true
    $scope.selected = {}

    $scope.alerts = []

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
        $scope.places.unshift do
            repr: ""
            id: 0

    $http.get "/api/shelfs"
    .then (response) !->
        $scope.shelfs = response.data
        $scope.shelfs.unshift do
            repr: ""
            id: 0

    $http.get "/api/publishers"
    .then (response) !->
        $scope.publishers = response.data

    $http.get "/api/distributors"
    .then (response) !->
        $scope.distributors = response.data
        $scope.distributors.unshift do
            repr: ""
            id: 0

    # Get cards in stock
    params = do
        order_by: "-created" # valid django
        language: $scope.language
        page_size: $scope.page_size
        page: $scope.page
    $http.get "/api/cards", do
        params: params
    .then (response) !->
        $scope.cards = response.data.cards
        $scope.meta = response.data.meta
        for elt in $scope.cards
            $scope.selected[elt.id] = false
            elt.date_publication = Date.parse(elt.date_publication)

        $scope.define_price_choices!

    $scope.validate = !->
        params = do
            query: $scope.query
            order_by: "-created"  # Should be by title for custom searches. Modified python-side.
            in_stock: true

        if $scope.publisher
            params.publisher_id = $scope.publisher.pk
        if $scope.place
            params.place_id = $scope.place.id
        if $scope.card_type
            params.card_type = $scope.card_type
        if $scope.shelf
            params.shelf_id = $scope.shelf.pk
        if $scope.distributor
            params.distributor_id = $scope.distributor.id
        if $scope.quantity_choice
            params.quantity_choice = $scope.quantity_choice.id
        if $scope.price_choice
            params.price_choice = $scope.price_choice.id
        if $scope.date_created
            params.date_created = $scope.date_created
            params.date_created_sort = $scope.date_created_sort.id
        params.page = $scope.page
        params.page_size = $scope.page_size

        $window.localStorage.page_size = $scope.page_size

        $http.get "/api/cards", do
            params: params
        .then (response) !->
            $scope.cards = response.data.cards
            $scope.meta = response.data.meta
            $window.document.getElementById("default-input").select()

    $scope.nextPage = !->
        if $scope.page < $scope.meta.num_pages
            $scope.page += 1
            $scope.validate!

    $scope.lastPage = !->
        $scope.page = $scope.meta.num_pages
        $scope.validate!

    $scope.previousPage = !->
        if $scope.page > 1
            $scope.page -= 1
            $scope.validate!

    $scope.firstPage =!->
        $scope.page = 1
        $scope.validate!

    # Add a checkbox column to select rows.
    $scope.toggleAll = !->
        for elt in $scope.cards
                $scope.selected[elt.id] = $scope.selectAll

        $scope.selectAll = not $scope.selectAll

    # Set focus:
    utils.set_focus!

    $window.document.title = "Abelujo - " + gettext("Stock")

    $scope.closeAlert = (index) !->
        $scope.alerts.splice index, 1

    $scope.toggle_images = !->
        $scope.show_images = not $scope.show_images
        $window.localStorage.show_images = $scope.show_images

    # This is needed for Django to process the params to its
    # request.POST dictionnary:
    $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded charset=UTF-8'

    # We need not to pass the parameters encoded as json to Django.
    # Encode them like url parameters.
    $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.
    config = do
        headers: { 'Content-Type': 'application/x-www-form-urlencoded charset=UTF-8'}

    ###################################
    ## Modale add selection to lists ##
    ###################################
    get_selected = ->
        to_add = Obj.filter (== true), $scope.selected
        |> Obj.keys

    $scope.add_to_lists = (size) !->
        to_add = get_selected!

        if not to_add.length
            alert "Please select some cards."
            return

        modalInstance = $uibModal.open do
            animation: $scope.animationsEnabled
            templateUrl: 'collectionModal.html'
            controller: 'CollectionModalControllerInstance'
            ## backdrop: 'static'
            size: size,
            resolve: do
                selected: ->
                    $scope.selected
                utils: ->
                    utils

        modalInstance.result.then (alerts) !->
            $scope.alerts = alerts
        , !->
              $log.info "modal dismissed"

    ##################################
    ## Bulk action on selection.    ##
    ##################################
    $scope.set_supplier = (card) !->
        cards_ids = get_selected!

        if not cards_ids.length
            alert "Please select some cards."
            return

        params = do
            cards_ids: join ",", cards_ids
        $http.post "/api/cards/set_supplier", params
        .then (response) !->
            $log.info "--- done"
            card_id = response.data.card_id
            $log.info $window.location.pathname
            $log.info response.data.url
            $window.location.pathname = $scope.language + response.data.url

        , (response) ->
            $log.info "--- error ", response.status, response.statusText


    ##############################
    # Keyboard shortcuts (hotkeys)
    ##############################
    hotkeys.bindTo($scope)
    .add do
        combo: "d"
        description: gettext "show or hide the book details in tables."
        callback: !->
            $scope.toggle_images!

    .add do
        combo: "s"
        description: gettext "go to the search box"
        callback: !->
            utils.set_focus!

]

angular.module "abelujo" .controller "CollectionModalControllerInstance", ($http, $scope, $uibModalInstance, $window, $log, utils, selected) !->

    {Obj, join, sum, map, filter, lines} = require 'prelude-ls'

    $scope.selected_baskets = {}
    $scope.alerts = []

    $http.get "/api/baskets"
    .then (response) !->
        $scope.baskets = response.data.data

    $scope.ok = !->

        to_add = Obj.filter (== true), selected
        |> Obj.keys

        coma_sep = join ",", to_add

        baskets_ids = $scope.selected_baskets
        |> Obj.filter ( -> it is true)
        |> Obj.keys

        params = do
            card_ids: coma_sep

        for b_id in baskets_ids
            $log.info "Adding cards to basket #{b_id}..."
            $http.post "/api/baskets/#{b_id}/add/", params
            .then (response) !->
                $scope.alerts = $scope.alerts.concat response.data.msgs

        $uibModalInstance.close($scope.alerts)


    $scope.cancel = !->
        $uibModalInstance.dismiss('cancel')

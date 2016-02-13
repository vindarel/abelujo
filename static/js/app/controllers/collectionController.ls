angular.module "abelujo.controllers", [] .controller 'collectionController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', '$cookies', '$uibModal', '$log', ($http, $scope, $timeout, utils, $filter, $window, $cookies, $uibModal, $log) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {Obj, join, sum, map, filter, lines} = require 'prelude-ls'

    $scope.query = ""
    $scope.cards = []
    $scope.places = []
    $scope.place = null
    $scope.categories = []
    $scope.category = null
    $scope.publisher = null
    $scope.baskets = []

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
            params['publisher_id'] = $scope.publisher.pk
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

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1


    # This is needed for Django to process the params to its
    # request.POST dictionnary:
    $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded charset=UTF-8'

    # We need not to pass the parameters encoded as json to Django.
    # Encode them like url parameters.
    $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.
    config = do
        headers: { 'Content-Type': 'application/x-www-form-urlencoded charset=UTF-8'}

    $scope.open = (size) !->
        to_add = Obj.filter (== true), $scope.selected
        |> Obj.keys

        if not to_add.length
            alert "Please select some cards first"
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
]

angular.module "abelujo" .controller "CollectionModalControllerInstance", ($http, $scope, $uibModalInstance, $window, $log, utils, selected) ->

    {Obj, join, sum, map, filter, lines} = require 'prelude-ls'

    $scope.selected_baskets = {}
    $scope.alerts = []

    $http.get "/api/baskets"
    .then (response) ->
        $scope.baskets = response.data.data

    $scope.ok = !->

        to_add = Obj.filter (== true), selected
        |> Obj.keys

        coma_sep = join ",", to_add

        baskets_ids = $scope.selected_baskets
        |> Obj.filter ( -> it is true)
        |> Obj.keys

        #  This is needed for Django to process the params to its
        #  request.POST dictionnary:
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

        #  We need not to pass the parameters encoded as json to Django.
        #  Encode them like url parameters.
        $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.
        config = do
            headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

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

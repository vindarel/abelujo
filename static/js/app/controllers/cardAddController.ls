angular.module "abelujo" .controller 'cardAddController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', ($http, $scope, $timeout, utils, $filter, $window) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines} = require 'prelude-ls'

    $scope.card = {}
    $scope.ready = false
    $scope.category = {}

    $scope.total_places = 0
    $scope.total_places_discount = 0
    $scope.total_deposits = 0

    # Current language ? for url redirection.
    $scope.language = utils.url_language($window.location.pathname)

    $scope.update_total_places = !->
        # total withOUT discount
        $scope.total_places = ($scope.places |> map (.quantity) |> sum ) * $scope.card.price
        $scope.total_places = $scope.total_places.toFixed 2

        # total with discount
        if $scope.distributor.selected
            $scope.total_places_discount = ($scope.places |> map (.quantity) |> sum ) * ($scope.card.price - $scope.card.price * $scope.distributor.selected.discount / 100)
            $scope.total_places_discount = $scope.total_places_discount.toFixed 2
        else
            console.log "must set the distributor first"

    $scope.update_total_deposits = !->
        $scope.total_deposits = $scope.deposits |> map (.quantity) |> sum

    re = /(\d)+/
    card_id = $window.location.pathname.match(re)
    $http.get "/api/card/" + card_id, do
        params: {}
    .then (response) !->
        $scope.card = response.data.data
        $scope.ready = true

    getDistributors = ->
        $http.get "/api/distributors", do
            params: do
                "query": ""
        .then (response) ->
            $scope.distributor_list = response.data
            $scope.distributor = $scope.distributor_list[0]
            response.data

    getDistributors()

    # Get deposits
    $http.get "/api/deposits/", do
        params: {}
    .then (response) !->
        $scope.deposits = response.data.data
        for dep in $scope.deposits
            dep.quantity = 0

    # Get places
    $http.get "/api/places/", do
        params: {}
    .then (response) !->
        $scope.places = response.data
        for place in $scope.places
            place.quantity = 0

    # Get baskets
    $http.get "/api/baskets/", do
        params: {}
    .then (response) !->
        $scope.baskets = response.data.data
        for it in $scope.baskets
            it.quantity = 0

    # Get categories
    $http.get "/api/categories/", do
        params: {}
    .then (response) !->
        $scope.categories = response.data

    $scope.filter_deposits = !->
        $scope.filtered_deposits = $scope.deposits |> filter (.distributor == $scope.distributor.selected.name)
        for depo in $scope.deposits
            depo.quantity = 0
        $scope.update_total_deposits()
        $scope.update_total_places()

    $scope.validate = ->
        #  Make Django to process the params to its request.POST dictionnary:
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        #  Don't give the parameters encoded as json to Django. Encode them like url parameters.
        $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.
        config = do
              headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        # Quantities per places: give the place id and its quantity
        places_ids_qties = []
        map ->
            places_ids_qties.push "#{it.id}, #{it.quantity}"
        , $scope.places

        # Baskets ids and their quantities
        baskets_ids_qties = []
        map ->
            baskets_ids_qties.push "#{it.id},#{it.quantity}"
        , $scope.baskets

        # Deposits ids and their quantities
        deposits_ids_qties = []
        map ->
            deposits_ids_qties.push "#{it.id},#{it.quantity}"
        , $scope.deposits

        params = do
            card_id: $scope.card_id
            distributor_id: $scope.distributor.id
            places_ids_qties: places_ids_qties
            deposits_ids_qties: deposits_ids_qties
            baskets_ids_qties: baskets_ids_qties

        if $scope.category.pk
            params.category_id = $scope.category.pk

        $http.post "/api/card/#{$scope.card.id}/add/", params
        .then (response) !->
            # $scope.alerts = response.data.alerts
            if response.status == 200
                $window.location.href = "/#{$scope.language}/search#{$window.location.search}"

    # Set focus:
    angular.element('#default-input').trigger('focus');

    $window.document.title = "Abelujo - " + gettext("Add a card")

]

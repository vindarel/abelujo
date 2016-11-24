# Copyright 2014 - 2016 The Abelujo Developers
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

angular.module "abelujo" .controller 'cardAddController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', ($http, $scope, $timeout, utils, $filter, $window) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines} = require 'prelude-ls'

    $scope.card = {}
    $scope.ready = false
    $scope.shelf = {}
    $scope.distributor = {}

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

    # Get the card
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
            if response.data.length == 0
                $scope.distributor = {}
            else
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

    # Get shelfs
    $http.get "/api/shelfs/", do
        params: {}
    .then (response) !->
        $scope.shelfs = response.data

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

        if $scope.shelf.pk
            params.shelf_id = $scope.shelf.pk

        $http.post "/api/card/#{$scope.card.id}/add/", params
        .then (response) !->
            # $scope.alerts = response.data.alerts
            if response.status == 200
                $window.location.href = "/#{$scope.language}/search##{$window.location.search}"

    # Set focus:
    angular.element('#default-input').trigger('focus');

    $window.document.title = "Abelujo - " + gettext("Add a card")

]

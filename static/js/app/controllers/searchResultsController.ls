# Copyright 2014 The Abelujo Developers
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

angular.module "abelujo" .controller 'searchResultsController', ['$http', '$scope', '$timeout', '$filter', '$window', '$uibModal', '$log', 'utils', ($http, $scope, $timeout, $filter, $window, $uibModal, $log, utils) !->

    {Obj, join, reject, sum, map, filter, lines} = require 'prelude-ls'

    $window.document.title = "Abelujo - " + gettext("search")
    $scope.language = utils.url_language($window.location.pathname)

    $scope.cards = []
    $scope.alerts = []
    $scope.selectAll = true
    $scope.datasources =
        * name: "librairiedeparis (fr)"
          id: "librairiedeparis"
        * name: "Decitre (fr)"
          id: "decitre"
        * name: "Casa del libro - es"
          id: "casadellibro"
    $scope.datasource = $scope.datasources[0]

    $scope.validate = !->
        params = do
            query: $scope.query

        $http.get "/api/datasource/search/", do
            params: params
        .then (response) !->
            $scope.cards = response.data.data
            for card in $scope.cards
                card.selected = false

    # Add a checkbox column to select rows.
    $scope.toggleAll = !->
        for card in $scope.cards
            # $scope.selected[i] = $scope.selectAll
            card.selected = $scope.selectAll

        $scope.selectAll = not $scope.selectAll


    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1

    # todo needed ?
    config = do
        headers: { 'Content-Type': 'application/x-www-form-urlencoded charset=UTF-8'}

    $scope.open = (size) !->
        to_add = Obj.filter (.selected == true), $scope.cards

        keys = Obj.keys to_add
        if not keys.length
            alert "Please select some cards first"
            return

        modalInstance = $uibModal.open do
            animation: $scope.animationsEnabled
            templateUrl: 'SearchResultsModal.html'
            controller: 'SearchResultsModalControllerInstance'
            ## backdrop: 'static'
            size: size,
            resolve: do
                selected: ->
                    to_add
                utils: ->
                    utils

        modalInstance.result.then (alerts) !->
            $scope.alerts = alerts
        , !->
              $log.info "modal dismissed"
]

angular.module "abelujo" .controller "SearchResultsModalControllerInstance", ($http, $scope, $uibModalInstance, $window, $log, utils, selected) ->

    {Obj, join, sum, map, filter, lines} = require 'prelude-ls'

    $scope.selected_baskets = {}
    $scope.alerts = []

    $http.get "/api/baskets"
    .then (response) ->
        $scope.baskets = response.data.data

    $scope.ok = !->

        to_add = selected # list of dicts

        baskets_ids = $scope.selected_baskets
        |> Obj.filter ( -> it is true)
        |> Obj.keys

        config = do
            headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        params = do
            cards: to_add

        for b_id in baskets_ids
            $log.info "Adding cards to basket #{b_id}..."
            $http.post "/api/baskets/#{b_id}/add/", params
            .then (response) !->
                $scope.alerts = $scope.alerts.concat response.data.msgs

        $uibModalInstance.close($scope.alerts)


    $scope.cancel = !->
        $uibModalInstance.dismiss('cancel')

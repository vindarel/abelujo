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

angular.module "abelujo" .controller 'searchResultsController', ['$http', '$scope', '$timeout', '$filter', '$window', '$uibModal', '$log', 'utils', '$location', 'hotkeys', ($http, $scope, $timeout, $filter, $window, $uibModal, $log, utils, $location, hotkeys) !->

    {Obj, join, reject, sum, map, filter, find, lines} = require 'prelude-ls'

    $scope.language = utils.url_language($window.location.pathname)

    $scope.cards = []
    $scope.alerts = []
    $scope.page = 1
    $scope.selectAll = true
    # warning, they must have the same id as their module's self.NAME.
    $scope.datasources =
        * name: "librairiedeparis - fr"
          id: "librairiedeparis"
        * name: "Decitre - fr"
          id: "decitre"
        * name: "Casa del libro - es"
          id: "casadellibro"
    $scope.datasource = $scope.datasources[0]
    $scope.results_page = [] # list of dicts with page and other search params.

    $scope.next_results = !->
        if not $scope.query
            return
        search_obj = $location.search()
        page = search_obj.page
        if not page
            page = "1"

        page = parseInt(page, 10)
        page += 1
        $scope.page = page
        $location.search('page', page)
        $scope.validate!

    $scope.previous_results = !->
        if not $scope.query
            return
        search_obj = $location.search()
        page = search_obj.page
        if not page
            page = "1"

        page = parseInt(page, 10)
        page -= 1
        if page < 1
            page = 1
        $scope.page = page
        $location.search('page', page)
        $scope.validate!

    $scope.validate = !->
        """Search for cards.
        """
        if not $scope.query
            return
        $location.search('q', $scope.query)
        $location.search('source', $scope.datasource.id)
        search_obj = $location.search()

        # Look at the history, for Previous button
        cache = $scope.results_page
        |> find ( -> it.page == $scope.page and it.query == $scope.query and it.datasource == $scope.datasource.id)
        if cache
            $scope.cards = cache.cards
            return

        params = do
            # query: $scope.query
            query: search_obj.q
            # datasource: $scope.datasource.id
            datasource: search_obj.source
            page: search_obj.page

        $http.get "/api/datasource/search/", do
            params: params
        .then (response) !->
            $window.document.title = "Abelujo - " + gettext("search") + " " + $scope.query
            $scope.cards = response.data.data
            for card in $scope.cards
                card.selected = false
            $scope.results_page.push do
                cards: $scope.cards
                page: $scope.page
                query: $scope.query
                datasource: $scope.datasource.id
        , (response) ->
            $scope.alerts.push do
                level: 'error'
                message: gettext "Internal error, sorry !"

    # Initial search results, read the url's query params after the #
    search_obj = $location.search()
    $scope.query = search_obj.q
    source_id = search_obj.source
    $scope.datasource = $scope.datasources
    |> find (.id == source_id)
    if not $scope.datasource
        $scope.datasource = $scope.datasources[0]
    $scope.validate!

    $window.document.title = "Abelujo - " + gettext("search") + " " + $scope.query

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

    $scope.create_and_add = (card) !->
        params = do
            card: card
        $http.post "/api/cards/create", params
        .then (response) ->
            card_id = response.data.card_id
            # Card created in DB. Now add it to places, deposits, etc.
            $window.location.href = "/#{$scope.language}/stock/card/create/#{card_id}?q=#{$scope.query}&source=#{$scope.datasource.id}"

        , (response) ->
            ... # error

    # Modal
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

    # Set focus:
    utils.set_focus!

    # Keyboard shortcuts (hotkeys)
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

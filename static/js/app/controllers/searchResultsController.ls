# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

angular.module "abelujo" .controller 'searchResultsController', ['$http', '$scope', '$timeout', '$filter', '$window', '$uibModal', '$log', 'utils', '$location', 'hotkeys', ($http, $scope, $timeout, $filter, $window, $uibModal, $log, utils, $location, hotkeys) !->

    {Obj, join, reject, sum, map, filter, find, lines} = require 'prelude-ls'

    $scope.language = utils.url_language($window.location.pathname)

    $scope.not_available_status =
        "Indisponible temporairement"
        "Indisponible"
        "Epuise"
        "epuise"
        "Epuisé"
        "epuisé"
        "06"
        "6"
        "7"
        "Manque sans date"
        ...

    $scope.is_not_available = (label) ->
        return label in $scope.not_available_status

    $scope.cards = []
    $scope.data = {}  # other objects: message, etc.
    $scope.alerts = []
    $scope.page = 1
    $scope.selectAll = true
    # warning, they must have the same id as their module's self.NAME.
    $scope.datasources =
        * name: "librairiedeparis - fr"
          id: "librairiedeparis"
        * name: "dilicom - fr"
          id: "dilicom"
        * name: "lelivre - ch"
          id: "lelivre"
        * name: "Casa del libro - es"
          id: "casadellibro"
        * name: "Belgique - be"
          id: "filigranes"
        ## * name: "Buchlentner - de"
        ##   id: "buchlentner"
        * name: "DVDs"
          id: "momox"
        * name: "discogs - CDs"
          id: "discogs"

    $scope.results_page = [] # list of dicts with page and other search params.
    $scope.show_images = true

    $scope.saveDatasource = !->
        $window.localStorage.setItem('datasource', $scope.datasource.id)

    $scope.details_url_for = (card) ->
        if card.in_stock is not null
           return card.get_absolute_url

        return card.details_url

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
        $scope.validate_with_query $scope.query

    $scope.validate_with_query = (query) !->
        """Search for cards.
        """
        if not query
            return
        $location.search('q', query)
        $location.search('source', $scope.datasource.id)
        search_obj = $location.search()

        # Look at the history, for Previous button
        cache = $scope.results_page
        |> find ( -> it.page == $scope.page and it.query == query and it.datasource == $scope.datasource.id)
        if cache
            $scope.cards = cache.cards
            $window.document.getElementById("default-input").select()
            return

        params = do
            query: query
            ## query: search_obj.q
            # datasource: $scope.datasource.id
            datasource: search_obj.source
            page: search_obj.page
            language: $scope.language

        $http.get "/api/datasource/search/", do
            params: params
        .then (response) !->
            $window.document.title = "Abelujo - " + gettext("search") + " " + query
            $scope.cards = response.data.data

            # select the input text, ready to accept another one.
            $window.document.getElementById("default-input").select()

            if response.data.data.length == 0
                $scope.no_results = true
            else
                $scope.no_results = false

            $scope.data = response.data

            for card in $scope.cards
                card.selected = false
            $scope.results_page.push do
                cards: $scope.cards
                page: $scope.page
                query: query
                datasource: $scope.datasource.id
        , (response) !->
            $scope.alerts.push do
                level: 'danger'
                message: gettext "Internal error, sorry ! We've been notified about it."

    # Initial search results, read the url's query params after the #
    search_obj = $location.search()
    # Re-search with the query (with a simple cache both here and at the backend),
    # but don't save it in $scope.query, to not populate the input field.
    # As a consequence, the value of query is set and retrieved with the url,
    # not with $scope.query.
    previous_query = search_obj.q
    source_id = search_obj.source
    if source_id
        $scope.datasource = $scope.datasources
        |> find (.id == source_id)
        if not $scope.datasource
            $scope.datasource = $scope.datasources[0]

    else
        datasource_id = $window.localStorage.getItem "datasource"
        if datasource_id
           $scope.datasource = $scope.datasources
           |> find ( -> it.id == datasource_id)
        else
           $scope.datasource = $scope.datasources[0]

    $scope.validate_with_query previous_query

    $window.document.title = "Abelujo - " + gettext("search") + " " + previous_query

    # Add a checkbox column to select rows.
    $scope.toggleAll = !->
        for card in $scope.cards
            # $scope.selected[i] = $scope.selectAll
            card.selected = $scope.selectAll

        $scope.selectAll = not $scope.selectAll

    $scope.toggle_images = !->
        $scope.show_images = not $scope.show_images

    $scope.closeAlert = (index) !->
        $scope.alerts.splice index, 1

    ##################################
    ## Create and add in new page   ##
    ##################################
    $scope.create_and_add = (card) !->
        params = do
            card: card
        $http.post "/api/cards/create", params
        .then (response) !->
            query = $location.search().q
            card_id = response.data.card_id
            # Card created in DB. Now add it to places, deposits, etc.
            if card_id
                $window.location.href = "/#{$scope.language}/stock/card/create/#{card_id}?q=#{query}&source=#{$scope.datasource.id}"
            else
                $scope.alerts.push do
                    level: 'danger'
                    message: gettext "Server error… sorry !"

        , (response) ->
            ... # error

    #####################################
    ## Create and command for client   ##
    #####################################
    $scope.create_and_command_client = (card) !->
        $log.info "card: ", card
        $log.info "isbn: ", card.isbn
        params = do
            card: card
        $http.post "/api/cards/create", params
        .then (response) !->
            card_id = response.data.card_id
            # Card created in DB. Now choose the client to command for.
            if card_id
                $window.location.href = "/#{$scope.language}/command/#{card_id}?q=#{$scope.query}&source=#{$scope.datasource.id}"
            else
                $scope.alerts.push do
                    level: 'danger'
                    message: gettext "Server error… sorry !"

        , (response) ->
            ... # error
    ########################################################
    # Add to Command
    ########################################################
    $scope.do_card_command = (isbn) !->
        # Need to create from the ISBN.
        if not isbn
            alert "Ce livre n'a pas d'ISBN ! Commande impossible."
            return
        $log.info "--- do_card_command ", isbn
        params = do
            isbn: isbn
            command: true
        $http.post "/api/cards/quickcreate/", params
        .then (response) !->
            $log.info response
            Notiflix.Notify.Success "Commandé"


    $scope.add_to_command = (size) !->
        to_add = Obj.filter (.selected == true), $scope.cards

        keys = Obj.keys to_add
        if not keys.length
            alert "Please select some cards first"
            return

        params = do
            cards: to_add
        $http.post "/api/baskets/1/add/", params
        .then (response) !->
            card_id = response.data.card_id

    ########################################################
    # Modal choose a list
    ########################################################
    $scope.open_list_select = (size) !->
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

    ########################################################
    # Modal choose an inventory
    ########################################################
    $scope.open_inv_select = (size) !->
        to_add = Obj.filter (.selected == true), $scope.cards

        keys = Obj.keys to_add
        if not keys.length
            alert "Please select some cards first"
            return

        modalInstance = $uibModal.open do
            animation: $scope.animationsEnabled
            templateUrl: 'SearchResultsAddToInventoryModal.html'
            controller: 'SearchResultsAddToInventoryModalController'
            ## backdrop: 'static'
            size: size,
            resolve: do
                cards_selected: ->
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

angular.module "abelujo" .controller "SearchResultsModalControllerInstance", ($http, $scope, $uibModalInstance, $window, $log, utils, selected) !->

    {Obj, join, sum, map, filter, lines, tail} = require 'prelude-ls'

    $scope.selected_baskets = {}
    $scope.alerts = []

    $http.get "/api/baskets"
    .then (response) !->
        $scope.baskets = tail response.data.data  # remove auto_command

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

angular.module "abelujo" .controller "SearchResultsAddToInventoryModalController", ($http, $scope, $uibModalInstance, $window, $log, utils, cards_selected) !->

    {Obj, join, sum, map, filter, lines} = require 'prelude-ls'

    $scope.inventory = undefined
    $scope.alerts = []

    #TODO: only get not closed ones.
    $http.get "/api/inventories"
    .then (response) !->
        $scope.inventories = response.data.data

    $scope.ok = !->

        to_add = cards_selected # list of dicts

        config = do
            headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        params = do
            cards: to_add

        $log.info "Adding cards to inventory #{$scope.inventory.id}..."
        $log.info "Adding cards", to_add
        $http.post "/api/inventories/#{$scope.inventory.id}/update/", params
        .then (response) !->
            $scope.alerts = $scope.alerts.concat response.data.msgs

        $uibModalInstance.close($scope.alerts)


    $scope.cancel = !->
        $uibModalInstance.dismiss('cancel')

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

angular.module "abelujo" .controller 'inventoryNewController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', 'hotkeys', ($http, $scope, $timeout, utils, $filter, $window, hotkeys) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines, reverse, join} = require 'prelude-ls'

    # The cards fetched from the autocomplete.
    $scope.cards_fetched = []
    # The autocomplete choice.
    $scope.copy_selected = undefined
    $scope.history = []
    # The cards "inventoried" of the current session: the ones
    # displayed. They are saved in the db instantly.
    $scope.cards_selected = []
    # All the cards inventoried, even the ones we don't want to show anymore.
    $scope.all = []
    # Boolean to show or hide all the cards (hide by default)
    $scope.showAll = false  # toggled by the checkbox itself.
    $scope.cards_to_show = []

    $scope.tmpcard = undefined
    # A list of already selected cards' ids
    $scope.selected_ids = []
    existing_card = undefined

    # If we're on page /../inventories/XX/, get info of inventory XX.
    #XXX use angular routing
    $scope.inv_id = utils.url_id($window.location.pathname) # the regexp could include "inventories"
    $scope.cur_inv = ""
    $scope.language = utils.url_language($window.location.pathname)

    $scope.setCardsToShow = !->
        " Show all the cards inventoried, or the current ones. "
        if $scope.showAll
            $scope.cards_to_show = $scope.all
            |> reverse
        else
            $scope.cards_to_show = $scope.cards_selected
            |> reverse

    $scope.toggleCardsToShow = !->
        $scope.showAll = ! $scope.showAll
        $scope.setCardsToShow!

    if $scope.inv_id

        $http.get "/api/inventories/#{$scope.inv_id}/"
        .then (response) ->
            response.data.data
            $scope.state = response.data.data
            $scope.cards_fetched = $scope.state.copies
            # To show every single card:
            map ->
                # it: has card and quantity properties only.
                $scope.all.push it.card
                $scope.all[* - 1].quantity = it.quantity
            , $scope.state.copies

            $scope.selected_ids = map (.card.id), $scope.state.copies
            $scope.total_missing = $scope.state.total_missing
            #XXX update the progress bar on the fly
            $scope.total_copies = $scope.state.total_copies
            $scope.total_missing = $scope.state.total_missing
            $scope.progress_current = $scope.state.total_copies / ($scope.total_missing + $scope.state.total_copies) * 100
            $scope.updateProgress($scope.total_copies, $scope.total_missing)
            $scope.progressStyle = do
                min-width: 4em
                width: $scope.progress_current + "%"

            $scope.cur_inv = $scope.state.inv_name

            return

    $scope.updateProgress = (current, missing) !->
        $scope.progress_current = current / (current + missing) * 100
        $scope.progress_current = $scope.progress_current.toFixed(1)

    $scope.getCards = (val) ->
        $http.get "/api/cards", do
            params: do
                query: val
                card_type_id: null
                lang: $scope.language
        .then (response) ->
            response.data.map (item) ->
                repr = "#{item.title}, #{item.authors_repr}, éd #{item.pubs_repr}"
                item.quantity = 1
                $scope.cards_fetched.push do
                    "repr": repr
                    "id": item.id
                    "item": item
                do
                    "repr": repr
                    "id": item.id

    # Add the choice of the autocomplete.
    # card_repr: the string representation.
    $scope.add_selected_card = (card_repr) !->
        $scope.tmpcard = _.filter $scope.cards_fetched, (it) ->
            it.repr == card_repr.repr
        $scope.tmpcard = $scope.tmpcard[0].item

        if not _.contains $scope.selected_ids, $scope.tmpcard.id
            $scope.cards_selected.push $scope.tmpcard
            $scope.all.push $scope.tmpcard
            $scope.selected_ids.push $scope.tmpcard.id

        else
            # existing_card = _.filter $scope.cards_selected, (it) ->
            existing_card = _.filter $scope.all, (it) ->
                it.id == $scope.tmpcard.id
            existing_card = existing_card[0]
            existing_card.quantity += 1

            # update the cards to display
            if not _.contains $scope.cards_selected, existing_card
                $scope.cards_selected.push existing_card

        $scope.copy_selected = undefined
        $scope.setCardsToShow() # needed for init

        $scope.save()

    $scope.remove_from_selection = (index_to_rm) !->
        """Remove the card from the selection to display
        and from the inventory (api call).
        """
        $scope.selected_ids.splice(index_to_rm, 1)
        $scope.cards_selected.splice(index_to_rm, 1)
        $scope.all.splice(index_to_rm, 1)
        focus()

        card = $scope.cards_to_show[index_to_rm]

        params = do
            "card_id": card.id
        $http.post "/api/inventories/#{$scope.inv_id}/remove/", params
        .then (response) !->
            $scope.cards_to_show.splice index_to_rm, 1
            # Update the progress bar.
            $scope.total_missing += 1
            $scope.total_copies -= 1
            $scope.updateProgress $scope.total_copies, $scope.total_missing

    $scope.updateCard = (index) !->
        """
        """
        card = $scope.cards_to_show[index]
        params = do
            "ids_qties": "#{card.id},#{card.quantity};"
        $http.post "/api/inventories/#{$scope.inv_id}/update/", params
        .then (response) !->
            $scope.cards_to_show.splice index_to_rm, 1
            # Update the progress bar.
            $scope.total_missing -= 1
            $scope.total_copies += 1
            $scope.updateProgress $scope.total_copies, $scope.total_missing

    $scope.save = ->
        """Send the new copies and quantities to be saved.
        """
        ids_qties = [] # a list of simple types, not list of dicts (see utils service)
        map  ->
            ids_qties.push "#{it.id}, #{it.quantity};"
        , $scope.cards_selected

        params = do
            "ids_qties": join "", ids_qties
        $http.post "/api/inventories/#{$scope.inv_id}/update/", params
        .then (response) !->
            $scope.alerts = response.data.msgs
            # Update the progress bar.
            $scope.total_missing -= $scope.cards_selected.length
            $scope.total_copies += $scope.cards_selected.length
            $scope.updateProgress($scope.total_copies, $scope.total_missing)
            # Reset the cards to display
            # $scope.cards_selected = []
            return response.data.status

    $scope.terminate = !->
        $http.get "/api/inventories/#{$scope.inv_id}/diff/"
        .then (response) !->
            $window.location.href = "/#{$scope.language}/inventories/#{$scope.inv_id}/terminate/"
    ######################
    # keyboard shortcuts
    # ####################
    hotkeys.bindTo($scope)
    .add do
        combo: "a"
        description: gettext "show all cards inventoried"
        callback: !->
            $scope.toggleCardsToShow!

    .add do
        combo: "s"
        description: gettext "go to the search box"
        callback: !->
           utils.set_focus!

    # Set focus:
    utils.set_focus!

    $window.document.title = "Abelujo - " + gettext("Inventory")

]

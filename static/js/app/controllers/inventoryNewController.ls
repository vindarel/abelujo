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

angular.module "abelujo" .controller 'inventoryNewController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', 'hotkeys', '$log', ($http, $scope, $timeout, utils, $filter, $window, hotkeys, $log) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    # Come on, I want a string.contains method.
    # String.prototype.contains = function(it) { return this.indexOf(it) != -1; }
    String.prototype.contains = (it) -> this.indexOf(it) != -1

    {sum, map, filter, lines, reverse, join, reject, round} = require 'prelude-ls'

    $scope.language = utils.url_language($window.location.pathname)

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
    showAll = $window.localStorage.getItem "inventories_showAll"
    if showAll != undefined
        if showAll == "true"
            $scope.showAll = true  # and activate the cards below (setCardsToShow)

    $scope.cards_to_show = []
    # Total value
    $scope.total_value = 0

    # Nb of cards and copies
    $scope.nb_cards = 0
    $scope.nb_copies = 0

    $scope.tmpcard = undefined
    # A list of already selected cards' ids
    $scope.selected_ids = []
    existing_card = undefined

    # pagination
    $scope.page = 1
    $scope.page_sizes = [25, 50, 100, 200]
    $scope.page_max = 1
    $scope.meta = do
        num_pages: null
        nb_results: null
    page_size = $window.localStorage.getItem "inventories_page_size"
    if page_size != null
        $scope.page_size = parseInt(page_size)
    else
        $scope.page_size = 25

    # ##############################################################################
    # This controller serves for all inventories, in all url:
    # inventories of shelves, places, baskets (/en/inventories/xx) and
    # inventorie of a command's parcel (/en/commands/xx/receive).
    # ##############################################################################
    is_default_inventory = false
    is_command_receive = false
    pathname = $window.location.pathname

    if pathname.contains "inventories"
        is_default_inventory = true
        $log.info "found default inventory"
        api_inventory_id = "/api/inventories/{inv_or_cmd_id}/"
        api_inventory_id_remove = api_inventory_id + "remove/"
        api_inventory_id_update = api_inventory_id + "update/"
        api_inventory_id_diff = api_inventory_id + "diff/"
        url_inventory_id_terminate = "/#{$scope.language}/inventories/{inv_or_cmd_id}/terminate/"
    else if pathname.contains "commands"
        is_command_receive = true
        $log.info "found a command inventory."
        api_inventory_id = "/api/commands/{inv_or_cmd_id}/receive/"
        api_inventory_id_remove = api_inventory_id + "remove/"
        api_inventory_id_update = api_inventory_id + "update/"
        api_inventory_id_diff = api_inventory_id + "diff/"
        url_inventory_id_terminate = "/#{$scope.language}/commands/{inv_or_cmd_id}/receive/terminate/"

    else
        $log.error "What are we doing the inventory of ??"
        ...

    get_api = (api) ->
        api.replace "{inv_or_cmd_id}", $scope.inv_or_cmd_id


    ##################### inventory controller #####################################
    # If we're on page /../inventories/XX/, get info of inventory XX.
    $scope.inv_or_cmd_id = utils.url_id($window.location.pathname) # the regexp could include "inventories"
    $log.info "found inv_or_cmd_id: ", $scope.inv_or_cmd_id
    $scope.cur_inv = ""

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
        $window.localStorage.inventories_showAll = $scope.showAll
        $scope.setCardsToShow!

    if $scope.inv_or_cmd_id

        $log.info "using api_inventory_id: ", get_api api_inventory_id
        params = do
            page_size: $scope.page_size
            page: $scope.page
        $http.get get_api(api_inventory_id), do
            params: params
        .then (response) ->
            $log.info "Response of api_inventory_id"
            response.data.data
            $scope.state = response.data.data
            $scope.cards_fetched = $scope.state.copies
            $scope.nb_cards = response.data.data.nb_cards
            $scope.nb_copies = response.data.data.nb_copies
            $scope.meta = response.data.data.meta
            # To show every single card:
            map ->
                # it: has card and quantity properties only.
                $scope.all.push it.card
                $scope.all[* - 1].quantity = it.quantity
            , $scope.state.copies

            $scope.selected_ids = map (.card.id), $scope.state.copies
            $scope.cur_inv = $scope.state.inv_name

            $scope.total_value = response.data.data.total_value
            return

    $scope.getCopies = !->
        params = do
            page_size: $scope.page_size
            page: $scope.page
        url = get_api api_inventory_id
        url += "copies"
        $http.get url, do
            params: params
        .then (response) !->
            $log.info "-- cards: ", response.data
            $scope.cards_fetched = response.data
            # cards_fetched: list of {cards:.., quantity:..}
            # Show the cards.
            $scope.all = []
            map ->
                # it: has card and quantity properties only.
                $scope.all.push it.card
                $scope.all[* - 1].quantity = it.quantity
            , response.data
            $scope.setCardsToShow!

    $scope.getCards = (val) ->
        $http.get "/api/cards", do
            params: do
                query: val
                card_type_id: null
                lang: $scope.language
        .then (response) ->
            res = response.data.cards.map (item) ->
                repr = "#{item.title}, #{item.authors_repr}, éd #{item.pubs_repr}"
                item.quantity = 1
                $scope.cards_fetched.push do
                    "repr": repr
                    "id": item.id
                    "item": item
                do
                    "repr": repr
                    "id": item.id

            if utils.is_isbn val and res.length == 1
               setTimeout( ->
                 $window.document.getElementById("default-input").value = ""
                 $scope.add_selected_card res[0]
               , 500)
               return

            return res

    # Add the choice of the autocomplete.
    $scope.add_selected_card = (card) !->
        $scope.tmpcard = _.filter $scope.cards_fetched, (it) ->
            it.repr == card.repr
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
        $scope.total_value += $scope.tmpcard.price * $scope.tmpcard.quantity
        $scope.total_value = round($scope.total_value * 10) / 10
        $scope.nb_cards += 1
        $scope.nb_copies += $scope.tmpcard.quantity

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
        $log.info "calling api_inventory_id_remove: ", api_inventory_id_remove
        $http.post get_api(api_inventory_id_remove), params
        .then (response) !->
            $scope.cards_to_show.splice index_to_rm, 1
            $scope.total_value -= card.price * card.quantity
            $scope.total_value = round($scope.total_value * 10) / 10
            $scope.nb_cards -= 1
            $scope.nb_copies -= card.quantity

    $scope.updateCard = (index) !->
        """
        """
        card = $scope.cards_to_show[index]
        params = do
            "ids_qties": "#{card.id},#{card.quantity};"

        $log.info "using api_inventory_id_update: ", api_inventory_id_update
        $http.post get_api(api_inventory_id_update), params
        .then (response) !->
            # update the total price. Since we listen for an ng-change
            # event, we don't know if we add or sub, so remove and add
            # again this card from the list.
            $log.info $scope.all
            thecard = $scope.all
            $scope.all = $scope.all
            |> reject (.id == card.id)
            $scope.all.push card
            $scope.total_value = response.data.total_value

            $scope.nb_cards = response.data.nb_cards
            $scope.nb_copies = response.data.nb_copies
            $scope.alerts = response.data.alerts

    $scope.save = ->
        """Send the new copies and quantities to be saved.
        """
        ids_qties = [] # a list of simple types, not list of dicts (see utils service)
        map  ->
            ids_qties.push "#{it.id}, #{it.quantity};"
        , $scope.cards_selected

        params = do
            "ids_qties": join "", ids_qties
        $http.post get_api(api_inventory_id_update), params
        .then (response) !->
            $scope.alerts = response.data.msgs
            # Reset the cards to display
            # $scope.cards_selected = []
            return response.data.status

    $scope.terminate = !->
        $log.info "using api_inventory_id_diff: ", api_inventory_id_diff
        $http.get get_api api_inventory_id_diff
        .then (response) !->
            $log.info "using url_inventory_id_terminate: ", get_api url_inventory_id_terminate
            $window.location.href = get_api url_inventory_id_terminate

    # Now that we have cards, show them...
    if $scope.showAll
        $scope.setCardsToShow!

    #########################################
    ## Pagination
    #########################################
    $scope.$watch "page_size", !->
        $window.localStorage.inventories_page_size = $scope.page_size
        $scope.getCopies!

    $scope.nextPage = !->
        if $scope.page < $scope.meta.num_pages
            $scope.page += 1
            $scope.getCopies!

    $scope.lastPage = !->
        $scope.page = $scope.meta.num_pages
        $scope.getCopies!

    $scope.previousPage = !->
        if $scope.page > 1
            $scope.page -= 1
            $scope.getCopies!

    $scope.firstPage =!->
        $scope.page = 1
        $scope.getCopies!

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

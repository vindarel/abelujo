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

angular.module "abelujo" .controller 'basketsController', ['$http', '$scope', '$timeout', '$filter', '$window', '$uibModal', '$log', 'utils', '$location', 'hotkeys', ($http, $scope, $timeout, $filter, $window, $uibModal, $log, utils, $location, hotkeys) !->

    {Obj, join, reject, sum, map, filter, find, lines, sort-by, find-index, reverse} = require 'prelude-ls'

    $scope.baskets = []
    $scope.copies = []
    $scope.alerts = []
    $scope.show_buttons = {}
    $scope.new_name = null
    $scope.cur_basket = undefined
    $scope.cards_fetched = [] # fetched from the autocomplete
    $scope.copy_selected = undefined
    $scope.show_images = false

    COMMAND_BASKET_ID = 1

    $scope.language = utils.url_language($window.location.pathname)

    $scope.showing_notes = false
    $scope.last_sort = "title"

    # pagination
    $scope.page = 1
    $scope.page_size = 25
    $scope.page_sizes = [25, 50, 100, 200]
    $scope.page_max = 1
    $scope.meta = do
        num_pages: null
        nb_results: null
    page_size = $window.localStorage.getItem "baskets_page_size"
    if page_size != null
        $scope.page_size = parseInt(page_size)

    $http.get "/api/baskets"
    .then (response) ->
        """Get the baskets, do not show the "to command" one, of id=1.
        """
        $scope.baskets = response.data.data
        |> reject (.id == 1)

        hash_basket_id = parseInt $location.hash(), 10
        index = find-index ( -> hash_basket_id == it.id), $scope.baskets
        if not index
            index = 0

        $scope.cur_basket_index = index
        $log.info "index: ", index
        $scope.showBasket index

    $scope.save_basket = !->
        params = do
            comment: $scope.cur_basket.comment

        $log.info "updating basket #{$scope.cur_basket.id}…"
        $http.post "/api/baskets/#{$scope.cur_basket.id}/update/", params
        .then (response) ->
            resp = response.data

    $scope.getCopies = (index) !->
        if $scope.cur_basket
            params = do
                page_size: $scope.page_size
                page: $scope.page
            $http.get "/api/baskets/#{$scope.cur_basket.id}/copies", do
                params: params
            .then (response) !->
                $scope.baskets[index].copies = response.data.data
                $scope.meta = response.data.meta
                $scope.copies = response.data.data

    $scope.showBasket = (index) !->
        "Show the copies of the given basket."
        $scope.cur_basket = $scope.baskets[index]
        if $scope.cur_basket
            $location.hash($scope.cur_basket.id)
            $window.document.title = "Abelujo - " + gettext("Baskets") + ", " + $scope.cur_basket.name
            # For the choose-shelf modale. We didn't find how to pass a custom parameter to it.
            $window.localStorage.setItem('cur_basket_id', $scope.cur_basket.id)

            if not $scope.cur_basket.copies
                $scope.getCopies index
            else
                $scope.copies = $scope.cur_basket.copies

            # Set focus.
            angular.element('#default-input').trigger('focus')

    $scope.archive_basket =  !->
        sure = confirm(gettext("Are you sure to archive this list {}?")replace "{}", $scope.cur_basket.name)
        if sure
            $http.post "/api/baskets/#{$scope.cur_basket.id}/archive"
            .then (response) !->
                index = find-index (.id == $scope.cur_basket.id), $scope.baskets
                $scope.baskets.splice index, 1
                if index >= $scope.baskets.length
                    index -= 1
                $scope.showBasket index

    $scope.delete_basket =  !->
        sure = confirm(gettext("You are going to delete the list {}. This can not be undone. Are you sure ?")replace "{}", $scope.cur_basket.name)
        $log.info sure
        if sure
            $http.post "/api/baskets/#{$scope.cur_basket.id}/delete"
            .then (response) !->
                index = find-index (.id == $scope.cur_basket.id), $scope.baskets
                $scope.baskets.splice index, 1
                if index >= $scope.baskets.length
                    index -= 1
                $scope.showBasket index

    $window.document.title = "Abelujo - " + gettext("Baskets")

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1

    $scope.getCards = (query) ->
        args = do
            query: query
            language: $scope.language
            lang: $scope.language

        promise = utils.getCards args
        promise.then (res) ->
            $scope.cards_fetched = res
            if utils.is_isbn query and res.length == 1
               setTimeout( ->
                 $window.document.getElementById("default-input").value = ""
                 $scope.add_selected_card res[0]
               , 700)
               return

            return res

    $scope.add_selected_card = (card) !->
        """ Add the card selected from the autocomplete to the current list's copies.
        Save it.
        """
        tmpcard = $scope.cards_fetched
        |> find (.repr == card.repr)
        tmpcard = tmpcard.item
        # $scope.copies.push tmpcard
        # Insert at the right sorted place
        index = 0
        index = find-index ( -> tmpcard.title < it.title), $scope.copies
        if not index
            index = $scope.copies.length
        $scope.copies.splice index, 0, tmpcard
        $scope.copy_selected = undefined
        # TODO: save
        $scope.save_card_to_basket tmpcard.id, $scope.cur_basket.id

    $scope.save_card_to_basket = (card_id, basket_id) !->
        # XXX seems redundant with save_quantity below
        coma_sep = "#{card_id}"
        params = do
            card_ids: coma_sep
        $http.post "/api/baskets/#{basket_id}/add/", params
        .then (response) !->
            $log.info "added cards to basket"
            # $scope.alerts = response.data.msgs # the confirmation alert should be less intrusive
        , (response) !->
            ... # error

    $scope.save_quantity = (index) !->
        """Save the item quantity.
        """
        # XXX see save_card_to_basket above
        card = $scope.copies[index]
        utils.save_quantity card, $scope.cur_basket.id

    $scope.command = !->
        """Add the copies of the current basket to the Command basket. Api call.
        """
        if not confirm gettext "You didn't set a supplier for this list (menu -> set a supplier). Do you want to carry on ?"
           return

        $log.info "cur_basket: ", $scope.cur_basket
        $log.info "copies: ", $scope.copies
        if not $scope.copies.length
            alert gettext "This basket has no copies to command !"
            return

        text = gettext("Do you want to mark all the cards of this list to command ?")
        if $scope.cur_basket.distributor
            text += gettext " They will be associated with the supplier #{$scope.cur_basket.distributor}."
        sure = confirm text
        if sure
            # We command all the basket.
            params = do
                basket_id: $scope.cur_basket.id
            $http.post "/api/baskets/#{COMMAND_BASKET_ID}/add/", params
            .then (response) !->
                # $scope.alerts = response.data.msgs
                $scope.alerts = response.data.alerts


    $scope.remove_from_selection = (index_to_rm) !->
        "Remove the card from the list. Server call to the api."
        card_id = $scope.copies[index_to_rm].id
        $http.post "/api/baskets/#{$scope.cur_basket.id}/remove/#{card_id}/",
        .then (response) !->
            $scope.copies.splice(index_to_rm, 1)
            # $scope.alerts = response.data.msgs # useless

        .catch (resp) !->
            $log.info "Error when trying to remove the card " + card_id

    $scope.get_data = ->
        # coma-sep list of ids:
        $scope.cur_basket.copies
        |> map (.id)
        |> join ","

    $scope.get_total_price = ->
        utils.total_price $scope.copies

    $scope.get_total_copies = ->
        utils.total_copies $scope.copies


    $scope.receive_command = !->
        if not $scope.cur_basket.distributor
           alert "You didn't set a distributor for this basket. Please see the menu Action -> set the supplier."
           return
        sure = confirm gettext "Do you want to receive a command for the supplier '#{$scope.cur_basket.distributor}' ?"
        if sure
            # Get or create the inventory, redirect to that inventory page
            $http.get "/api/baskets/#{$scope.cur_basket.id}/inventories/"
            .then (response) !->
                inv_id = response.data.data.inv_id
                # What url scheme ? We want to include the inv id to re-use the inventory controller.
                # baskets/<basket_id>/inventory/<inv id>/, or
                #  /inventories/<inv id>
                # $window.location.href = "/#{$scope.language}/baskets/#{$scope.cur_basket.id}/receive/"
                $window.location.href = "/#{$scope.language}/inventories/#{inv_id}/"

    $scope.return_to_supplier = !->
        if not $scope.cur_basket.distributor
           alert "You didn't set a distributor for this basket. Please see the menu Action -> set the supplier."
           return
        sure = confirm gettext "Do you want to return this basket to #{$scope.cur_basket.distributor} ? This will remove the given quantities from your stock."
        if sure
            $http.post "/api/baskets/#{$scope.cur_basket.id}/return"
            .then (response) !->
                $log.info response
                $scope.alerts = response.data.alerts
                # if response.data.status == "success" …

    #########################################
    ## Pagination
    #########################################
    $scope.$watch "page_size", !->
        $window.localStorage.baskets_page_size = $scope.page_size
        $scope.getCopies $scope.cur_basket_index

    $scope.nextPage = !->
        if $scope.page < $scope.meta.num_pages
            $scope.page += 1
            $log.info "-- cur_basket_index: ", $scope.cur_basket_index
            $scope.getCopies $scope.cur_basket_index

    $scope.lastPage = !->
        $scope.page = $scope.meta.num_pages
        $scope.getCopies $scope.cur_basket_index

    $scope.previousPage = !->
        if $scope.page > 1
            $scope.page -= 1
            $scope.getCopies $scope.cur_basket_index

    $scope.firstPage =!->
        $scope.page = 1
        $scope.getCopies $scope.cur_basket_index


    #############################
    # Open new basket modal
    # ###########################
    $scope.open_new_basket = (size) !->
        # angular.element('#modal-input').trigger('focus')  # noop :(
        modalInstance = $uibModal.open do
            animation: $scope.animationsEnabled
            templateUrl: 'basketModal.html'
            controller: 'BasketModalControllerInstance'
            ## backdrop: 'static'
            size: size,
            resolve: do
                utils: ->
                    utils

        modalInstance.result.then (basket) !->
            $scope.baskets.push basket
            $log.info "new basket: ", basket
            $log.info "all baskets: ", $scope.baskets
            ## $scope.showBasket basket.id  # doesn't work :(
        , !->
            $log.info "modal dismissed"

    #############################
    # Choose and add to shelf modal
    # ###########################
    ## $scope.add_to_shelf = (size) !->
    $scope.add_to_shelf = (cur_basket_id) !->
        $log.info "add_to_shelf got basket id", cur_basket_id
        modalInstance = $uibModal.open do
            animation: $scope.animationsEnabled
            templateUrl: 'chooseShelfModal.html'
            controller: 'ChooseShelfModalControllerInstance'
            ## backdrop: 'static'
            ## size: size,
            cur_basket_id: cur_basket_id,
            resolve: do
                utils: ->
                    utils

        modalInstance.result.then (basket) !->
            # Empty the basket (double work from the api).
            basket = $scope.baskets[cur_basket_id]
            basket.copies = []
            $scope.copies = []
            $log.info "modal ok"
        , !->
            $log.info "modal dismissed"

    $scope.toggle_images = !->
        $scope.show_images = not $scope.show_images

    $scope.sort_by = (key) !->
        if $scope.last_sort == key
            $scope.copies = $scope.copies
            |> reverse
        else
            $scope.copies = $scope.copies
            |> sort-by ( -> it[key])
            $scope.last_sort = key

        $log.info $scope.copies

    ##############################
    # Keyboard shortcuts (hotkeys)
    # ############################
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

    .add do
        combo: "n"
        description: gettext "hide or show your notes"
        callback: !->
            $scope.showing_notes = ! $scope.showing_notes

    .add do
        combo: "C"
        description: gettext "Create a new list"
        callback: !->
            $scope.open!

]

#####################
# New basket modal
# ###################
angular.module "abelujo" .controller "BasketModalControllerInstance", ($http, $scope, $uibModalInstance, $window, $log, utils) !->

    utils.set_focus!

    $scope.ok = !->
        if typeof ($scope.new_name) == "undefined" || $scope.new_name == ""
            $uibModalInstance.dismiss('cancel')
            return

        params = do
            name: $scope.new_name

        $http.post "/api/baskets/create", params
        .then (response) !->
            basket = response.data.data
            $scope.alerts = response.data.alerts
            $uibModalInstance.close(basket)

    $scope.cancel = !->
        $uibModalInstance.dismiss('cancel')

#####################
# Choose/add to shelf modal
# ###################
angular.module "abelujo" .controller "ChooseShelfModalControllerInstance", ($http, $scope, $uibModalInstance, $window, $log, utils) !->

    utils.set_focus!
    $scope.shelves = []
    $scope.selected_shelf = null

    $log.info "cur_basket_id storage: ", $window.localStorage.getItem('cur_basket_id')
    $scope.cur_basket_id = $window.localStorage.getItem('cur_basket_id')

    $http.get "/api/shelfs"
    .then (response) ->
        $log.info "response: ", response
        $scope.shelves = response.data
        $log.info "shelves: ", $scope.shelves

    $scope.ok = !->
        if typeof ($scope.selected_shelf) == "undefined" || $scope.selected_shelf == ""
            $uibModalInstance.dismiss('cancel')
            return

        $log.info "selected shelf: ", $scope.selected_shelf

        #  This is needed for Django to process the params to its
        #  request.POST dictionnary:
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

        #  We need not to pass the parameters encoded as json to Django.
        #  Encode them like url parameters.
        $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.
        config = do
            headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        params = do
            shelf_id: $scope.selected_shelf.pk

        $http.post "/api/baskets/#{$scope.cur_basket_id}/add_to_shelf/", params
        .then (response) !->
            $scope.alerts = response.data.alerts
            $uibModalInstance.close()
            $scope.alerts = response.data.alerts

    $scope.cancel = !->
        $uibModalInstance.dismiss('cancel')
        $scope.alerts = response.data.alerts

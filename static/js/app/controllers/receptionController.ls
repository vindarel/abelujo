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

angular.module "abelujo" .controller 'receptionController', ['$http', '$scope', '$timeout', '$filter', '$window', '$uibModal', '$log', 'utils', '$location', 'hotkeys' ($http, $scope, $timeout, $filter, $window, $uibModal, $log, utils, $location, hotkeys) !->

    {Obj, Str, join, reject, sum, map, filter, find, lines, sort-by, find-index, reverse} = require 'prelude-ls'

    $scope.shelves = []
    $scope.shelves_length = {}
    $scope.new_shelf = null
    $scope.cur_basket = do
      id: 0
      fields: {name: "Tous les titres"}

    $scope.cur_basket_index = 0

    $scope.copies = []  # current visible ones.
    $scope.all_copies = []  # all from reception.
    $scope.cards_fetched = []  # from user input
    $scope.copy_selected = undefined

    $scope.show_buttons = {}
    $scope.copy_selected = undefined
    $scope.show_images = false
    $scope.language = utils.url_language($window.location.pathname)
    $window.document.title = "Abelujo - " + gettext("Reception")

    # pagination
    $scope.page = 1
    $scope.page_size = 200
    $scope.page_sizes = [25, 50, 100, 200]
    $scope.page_max = 1
    $scope.meta = do
        num_pages: null
        nb_results: null
    page_size = $window.localStorage.getItem "baskets_page_size"
    if page_size != null
        $scope.page_size = parseInt(page_size)


    Notiflix.Notify.Init do
        timeout: 7000
        messageMaxLength: 220

    $http.get "/api/shelfs"
    .then (response) ->
        """
        Get the shelves.
        """
        $scope.shelves = response.data
        $log.info response.data
        ## hash_basket_id = parseInt $location.hash(), 10
        ## index = find-index ( -> hash_basket_id == it.id), $scope.baskets
        ## if not index
            ## index = 0

        ## $scope.cur_basket_index = index
        ## $log.info "index: ", index
        ## $scope.showBasket index

    # Get the cards of the current reception (ongoing one, not closed).
    $http.get "/api/reception/"
    .then (response) ->
          $log.info response
          $scope.all_copies = response.data.data
          $scope.copies = response.data.data

          $scope.get_basket_quantity!

          # Do they all have a shelf?
          for copy in $scope.copies
              if not copy.shelf
                 copy.alerts = []
                 copy.alerts.push do
                   message: "no shelf"

    # Get the shelves' "length" (how many cards in each).
    $http.get "/api/reception/shelfs"
    .then (response) ->
          $log.info response
          $scope.shelves_length = response.data.data

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
        """
        Add the card selected from the autocomplete to the current list's copies.
        And then, save it. If there is an error at this phase, show it asynchronously.
        """
        # We got a card from the autocomplete, we first want to display it.
        $log.info "adding ", card
        now = luxon.DateTime.local().toFormat('yyyy-LL-dd HH:mm:ss')
        tmpcard = $scope.cards_fetched
        |> find (.repr == card.repr)
        tmpcard = tmpcard.item  # object
        existing = $scope.all_copies
        |> find (.id == tmpcard.id)
        $log.info "exsting: ", existing  # array
        if existing
           existing.basket_qty += 1  # and move to top
           existing.modified = now
           index = find-index ( -> existing.id == it.id ), $scope.all_copies
           if index
               # remove existing from list
               $scope.all_copies.splice index, 1
               # and move to top.
               $scope.all_copies.unshift existing
        else
           tmpcard.modified = now
           $scope.all_copies.unshift tmpcard
           existing = tmpcard

        # Increment count of shelf, update badge.
        $scope.shelves_length[tmpcard.shelf_id] += 1
        $scope.copy_selected = undefined

        # If we add a book from a shelf menu but the book already has a different shelf,
        # show a message.
        if $scope.cur_basket.fields and existing.shelf_id and $scope.cur_basket.pk != existing.shelf_id
            title = Str.take 20 existing.title
            Notiflix.Notify.Info("Attention vous êtes dans le menu '#{$scope.cur_basket.fields.name}' et le livre '#{title}' a déjà un rayon ('#{existing.shelf}').")

        # Now, we want to register the card in the reception list.
        $scope.save_card_to_reception tmpcard.id

    # Save the card with its shelf.
    $scope.save_card_to_reception = (card_id) !->
        params = do
            card_id: card_id
            shelf_id: $scope.cur_basket.pk
        $http.post "/api/reception/add/", params
        .then (response) !->
            $log.info "added cards to reception"
            # $scope.alerts = response.data.msgs # the confirmation alert should be less intrusive
            card = $scope.all_copies
            |> find (.id == card_id)
            if card
                card.alerts = response.data.alerts
                $log.info "card alerts: ", card.alerts, "response: ", response.data
            else
                $log.info "PAS DE CARD !"
            Notiflix.Notify.Success "Card received!"

        , (response) !->
            Notiflix.Notify.Warning "Something went wrong."
            elt = $window.document.getElementById "card#{tmpcard.id}"


    $scope.getCopies = (id) !->
        $log.info "getCopies ", id
        res = $scope.all_copies
        |> filter (.shelf_id == id)
        $log.info "filtering all_copies: ", res
        $scope.copies = res
        return res

    $scope.showBasket = (index) !->
        "Show the copies of the shelf (by its index in the shelves list)."
        # Show all.
        $log.info "showBasket index in list ", index
        if index == 0
            $scope.copies = $scope.all_copies
            $scope.cur_basket_index = 0
            $scope.cur_basket = do
              id: 0
            return

        # Filter by shelf.
        $scope.cur_basket = $scope.shelves[index]
        $log.info "found shelf: ", $scope.cur_basket, "pk: ", $scope.cur_basket.pk
        if $scope.cur_basket
            $location.hash($scope.cur_basket.id)
            ## if not $scope.cur_basket.copies
                ## $scope.getCopies $scope.cur_basket.pk
            ## else
                ## $scope.copies = $scope.cur_basket.copies
            $scope.getCopies $scope.cur_basket.pk

            # Set focus.
            $scope.set_focus!

    $scope.showShelfById = (pk) ->
        # Similar to showBasket, but we got its pk, not its index.
        shelf = $scope.shelves
        |> find (.pk == pk)
        if shelf
           $log.info shelf
           ## $scope.showBasket shelf.pk
           $scope.cur_basket = shelf
           $scope.getCopies shelf.pk
           $scope.set_focus!

    $scope.update_card_shelf = (card, shelf) !->
        $log.info "got card: ", card, "new shelF: ", $scope.new_shelf, "arg: ", shelf
        params = do
            card_id: card.id
            shelf_id: shelf.pk
        $http.post "/api/cards/update", params
        .then (response) !->
            copy = $scope.all_copies
            |> find (.id == card.id)
            $log.info "updated card"
            copy.shelf = shelf.fields.name
            copy.shelf_id = shelf.pk
            copy.alerts = []
            Notiflix.Notify.Success "Shelf updated."

        , (response) !->
            Notiflix.Notify.Warning "Something went wrong."

    $scope.set_focus = !->
        # Set focus.
        angular.element('#default-input').trigger('focus')
    $scope.set_focus!

    $scope.save_quantity = (index) !->
        """Save the item quantity after click."""
        #TODO:
        card = $scope.copies[index]
        now = luxon.DateTime.local().toFormat('yyyy-LL-dd HH:mm:ss')
        utils.save_quantity card, $scope.cur_basket.id, is_box = $scope.boxes_page
        card.modified = now  # there is no success check

    ##############################
    # Keyboard shortcuts (hotkeys)
    # ############################
    hotkeys.bindTo($scope)
    .add do
        combo: "d"
        description: gettext "show or hide the book details in tables."
        callback: !->
            $scope.toggle_images!

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

    ############# toggle covers ###################
    $scope.toggle_images = !->
        $scope.show_images = not $scope.show_images


]
# Copyright 2014 - 2019 The Abelujo Developers
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

angular.module "abelujo" .controller 'basketToCommandController', ['$http', '$scope', '$timeout', 'utils', '$window', '$log', 'hotkeys', ($http, $scope, $timeout, utils, $window, $log, hotkeys) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {find, sum, map, filter, lines, group-by, join} = require 'prelude-ls'

    # url encodings for "mailto"
    NEWLINE = "%0D%0A"
    ESPERLUETTE = "%26"

    AUTO_COMMAND_ID = 1
    $scope.alerts = []
    $scope.distributor = {} # the distributor of this page.
    $scope.distributor_id = -1
    $scope.cards = []
    $scope.sorted_cards = {}
    $scope.body = ""  # email body.

    $scope.page = 1
    # $scope.page_size = 25  # fixed
    $scope.nb_results = 0
    $scope.page_max = 1
    $scope.page_size = 100  # also used in template.
    $scope.meta = do
        num_pages: null
        nb_results: null

    $scope.language = utils.url_language($window.location.pathname)
    $scope.show_images = false

    $scope.distributor_id = utils.url_id $window.location.pathname
    $log.info $scope.distributor_id

    # Get the distributor.
    if $scope.distributor_id != "0"
        $http.get "/api/distributors/#{$scope.distributor_id}"
        .then (response) !->
            $scope.distributor = response.data.data
            $log.info "-- dist: ", response.data.data
    else
        $scope.distributor = do
            name: "No supplier"
            id: 0
            repr: "No supplier"
            get_absolute_url: ""

    # Get the cards to command of this supplier.
    # supplier = distributor. If you want to use a publisher, set it as a distributor.
    getCards = !->
        params = do
            page: $scope.page
            page_size: $scope.page_size
            dist_id: -1
        $http.get "/api/commands/supplier/#{$scope.distributor_id}/copies", do
            params: params
        .then (response) !->
            $scope.cards = response.data.data
            $scope.totals = response.data.totals
            $scope.meta.num_pages = response.data.num_pages
            $scope.meta.nb_results = response.data.nb_results
            $log.info "cards: ", $scope.cards
            $log.info "-- meta: ", $scope.meta

    getCards!


    $scope.save_quantity = (index) !->
        # model card.basket_qty is saved.
        $log.info "--- save_quantity "
        card = $scope.cards[index]
        $log.info "saving ", card
        # we still save on the autocommand basket which mixes different distributors.
        utils.save_quantity card, AUTO_COMMAND_ID

    $scope.closeAlert = (index) !->
        $scope.alerts.splice index, 1

    $scope.get_body = ->
        "Get the list of cards and their quantities for the email body.
        "
        body = ""
        for card in $scope.cards
            body += "#{card.threshold} x #{card.title} ( #{card.price} €)" + NEWLINE

        total_price = 0
        total_price = $scope.cards
        |> filter (.threshold > 0)
        |> map ( -> it.price * it.threshold)
        |> sum

        discount = 0
        discount = $scope.distributor.discount
        total_discount = total_price - total_price * discount / 100

        body = body.replace "&", ESPERLUETTE # beware other encoding pbs
        body += NEWLINE + gettext("total price: ") + total_price + " €"
        body += NEWLINE + gettext("total with {}% discount: ").replace("{}", discount) + total_discount + " €"
        body += NEWLINE + gettext("Thank you.")
        $scope.body = body
        body

    $scope.remove_from_selection = (dist_name, index_to_rm) !->
        "Remove the card from the list. Server call."
        sure = confirm(gettext("Are you sure to remove the card '{}' from the command basket ?").replace("{}", $scope.cards[index_to_rm].title))
        if sure
            card_id = $scope.cards[index_to_rm].id
            $http.post "/api/baskets/#{AUTO_COMMAND_ID}/remove/#{card_id}/",
            .then (response) !->
                $scope.cards.splice(index_to_rm, 1)

            .catch (resp) !->
                $log.info "Error when trying to remove the card " + card_id

    $scope.validate_command = !->
        """Validate the command. We'll wait for it. Remove the list from the ToCommand basket.
        """
        if confirm gettext "Do you want to order this command for #{$scope.distributor.name} ?\n
            The cards will be removed from this list."
            $log.info "validate " + $scope.distributor.name
            cards = $scope.cards
            ids_qties = []
            map ->
                ids_qties.push "#{it.id}, #{it.basket_qty}"
            , cards
            $log.info "card ids_qties: " + ids_qties

            params = do
                ids_qties: ids_qties
                distributor_id: $scope.distributor_id
                foo: 1

            $http.post "/api/commands/create/", params # right ?
            .then (response) !->
                $log.info response.data
                if response.data.status == 'success'
                    $log.info "success !"
                    #TODO: redirect
                    $scope.cards = []

                else
                    $scope.alerts = response.data.alerts

    $scope.dist_href = (name) !->
        $window.location.href = "#" + name

    $scope.toggle_images = !->
        $scope.show_images = not $scope.show_images

    $scope.add_selected_card = (card_obj) !->
        $log.info "selected: ", card_obj

        # Add this card to the command.
        # If it doesn't have a distributor, assign it.
        params = do
            language: $scope.language
            card_id: card_obj.id
            dist_id: $scope.distributor_id
        $http.post "/api/v2/baskets/#{AUTO_COMMAND_ID}/add/", do
            params: params
        .then (response) ->
            # Add card to supplier's list.
            $log.info "-- card_obj ", card_obj
            $scope.alerts = response.data.alerts

            if response.data.card
                updated_card = response.data.card  # with new distributor
                # updated_card.quantity = 1
                updated_card.basket_qty = 1
                $log.info "updated_card: ", updated_card
                $scope.cards.unshift updated_card


    #########################################
    ## Pagination
    #########################################
    $scope.nextPage = !->
        if $scope.page < $scope.meta.num_pages
            $scope.page += 1
            getCards!

    $scope.lastPage = !->
        $scope.page = $scope.meta.num_pages
        getCards!

    $scope.previousPage = !->
        if $scope.page > 1
            $scope.page -= 1
            getCards!

    $scope.firstPage =!->
        $scope.page = 1
        getCards!

    ##############################
    # Keyboard shortcuts (hotkeys)
    # ############################
    hotkeys.bindTo($scope)
    .add do
        combo: "d"
        description: gettext "show or hide the book details in tables."
        callback: !->
            $scope.toggle_images!

    ##############################
    # Tour
    ##############################
    tour = new Tour do
        storage: false  # doesn't prevent to start from last step the second time.
        steps:
          * element: "\#suppliers",
            title: gettext "Commands",
            content: gettext "The commands are grouped by supplier."
          * element: "\#export",
            title: gettext "Export",
            content: gettext "You can export the list of commands as pdf or csv."
          * element: "\#ok",
            title: gettext "Register the command."
            content: gettext "You can send a pre-filled email to your supplier or download a document and send it by yourself. When you've done it, click OK."
          * element: "\#ongoing"
            title: gettext "Ongoing commands"
            content: gettext "Now, you can follow each command and change their status, to be sure it's been received and paid."
            placement: "bottom"

    # Initialize the tour

    $scope.start_tour = !->
        tour.init()
        tour.setCurrentStep(0)  # the second time would start from the end.
        # Start the tour
        tour.start(true)

    # Set focus:
    # angular.element('#default-input').trigger('focus')

    $window.document.title = "Abelujo - " + gettext("To command")


]

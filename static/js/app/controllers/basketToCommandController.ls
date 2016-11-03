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
    $scope.cards = []
    $scope.sorted_cards = {}
    $scope.distributors = []
    $scope.grouped_dist = {}
    $scope.bodies = {} # dist_id, email body

    $scope.language = utils.url_language($window.location.pathname)
    $scope.show_images = false

    $http.get "/api/baskets/#{AUTO_COMMAND_ID}/copies",
    .then (response) ->
        $scope.cards = response.data
        $scope.sorted_cards = group-by (.distributor.name), $scope.cards

    $http.get "/api/distributors",
    .then (response) !->
        $scope.distributors = response.data
        $scope.grouped_dist = group-by (.name), $scope.distributors

    $scope.save_quantity = (dist_name, index) !->
        dist_id = grouped_dist[dist_name][0].id
        card = $scope.sorted_cards[dist_id][index]
        utils.save_quantity card, AUTO_COMMAND_ID

    $scope.get_total_copies = (dist_name) ->
        copies = $scope.sorted_cards[dist_name]
        utils.total_copies copies

    $scope.get_total_price = (dist_name) ->
        copies = $scope.sorted_cards[dist_name]
        total = utils.total_price(copies)
        return total

    $scope.get_total_price_discounted = (dist_name) ->
        utils.total_price_discounted $scope.sorted_cards[dist_name]

    $scope.super_total_copies = ->
        utils.total_copies $scope.cards

    $scope.super_total_price = ->
        utils.total_price $scope.cards

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1

    $scope.get_body = (dist_name) ->
        "Get the list of cards and their quantities for the email body.
        "
        cards = $scope.sorted_cards[dist_name]
        |> filter (.threshold > 0)
        body = ""
        for card in cards
            body += "#{card.threshold} x #{card.title} ( #{card.price} €)" + NEWLINE

        total_price = 0
        total_price = cards
        |> filter (.threshold > 0)
        |> map ( -> it.price * it.threshold)
        |> sum

        discount = 0
        pub = find (.id == parseInt($scope.sorted_cards[dist_name][0].distributor.id, 10)), $scope.distributors
        discount = pub.discount
        total_discount = total_price - total_price * discount / 100

        body = body.replace "&", ESPERLUETTE # beware other encoding pbs
        body += NEWLINE + gettext("total price: ") + total_price + " €"
        body += NEWLINE + gettext("total with {}% discount: ").replace("{}", discount) + total_discount + " €"
        body += NEWLINE + gettext("Thank you.")
        $scope.bodies[dist_name] = body
        body

    $scope.remove_from_selection = (dist_name, index_to_rm) !->
        "Remove the card from the list. Server call."
        sure = confirm(gettext("Are you sure to remove the card '{}' from the command basket ?").replace("{}", $scope.sorted_cards[dist_name][index_to_rm].title))
        if sure
            card_id = $scope.sorted_cards[dist_name][index_to_rm].id
            $http.post "/api/baskets/#{AUTO_COMMAND_ID}/remove/#{card_id}/",
            .then (response) !->
                $scope.sorted_cards[dist_name].splice(index_to_rm, 1)

            .catch (resp) !->
                $log.info "Error when trying to remove the card " + card_id

    $scope.dist_href = (name) ->
        $window.location.href = "#" + name

    $scope.toggle_images = !->
        $scope.show_images = not $scope.show_images

    ##############################
    # Keyboard shortcuts (hotkeys)
    # ############################
    hotkeys.bindTo($scope)
    .add do
        combo: "d"
        description: gettext "show or hide the book details in tables."
        callback: !->
            $scope.toggle_images!

    # Set focus:
    # angular.element('#default-input').trigger('focus')

    $window.document.title = "Abelujo - " + gettext("To command")


]

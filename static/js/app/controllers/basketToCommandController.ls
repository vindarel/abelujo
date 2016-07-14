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

angular.module "abelujo" .controller 'basketToCommandController', ['$http', '$scope', '$timeout', 'utils', '$window', '$log', ($http, $scope, $timeout, utils, $window, $log) !->
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

    $http.get "/api/baskets/#{AUTO_COMMAND_ID}/copies",
    .then (response) ->
        $scope.cards = response.data
        $scope.sorted_cards = group-by (.distributor.id), $scope.cards

    $http.get "/api/distributors",
    .then (response) !->
        $scope.distributors = response.data
        $scope.grouped_dist = group-by (.id), $scope.distributors

    $scope.save_quantity = (dist_id, index) !->
        card = $scope.sorted_cards[dist_id][index]
        utils.save_quantity card, AUTO_COMMAND_ID

    $scope.get_total_copies = (dist_id) ->
        copies = $scope.sorted_cards[dist_id]
        utils.total_copies copies

    $scope.get_total_price = (dist_id) ->
        copies = $scope.sorted_cards[dist_id]
        total = utils.total_price(copies)
        return total

    $scope.super_total_copies = ->
        utils.total_copies $scope.cards

    $scope.super_total_price = ->
        utils.total_price $scope.cards

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1

    $scope.get_body = (dist_id) ->
        "Get the list of cards and their quantities for the email body.
        "
        cards = $scope.sorted_cards[dist_id]
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
        pub = find (.id == parseInt(dist_id, 10)), $scope.distributors
        discount = pub.discount
        total_discount = total_price - total_price * discount / 100

        body = body.replace "&", ESPERLUETTE # beware other encoding pbs
        body += NEWLINE + gettext("total price: ") + total_price + " €"
        body += NEWLINE + gettext("total with {}% discount: ").replace("{}", discount) + total_discount + " €"
        body += NEWLINE + gettext("Thank you.")
        $scope.bodies[dist_id] = body
        body

    $scope.remove_from_selection = (dist_id, index_to_rm) !->
        "Remove the card from the list. Server call."
        sure = confirm(gettext("Are you sure to remove the card '{}' from the command basket ?").replace("{}", $scope.sorted_cards[dist_id][index_to_rm].title))
        if sure
            card_id = $scope.sorted_cards[dist_id][index_to_rm].id
            $http.post "/api/baskets/#{AUTO_COMMAND_ID}/remove/#{card_id}/",
            .then (response) !->
                $scope.sorted_cards[dist_id].splice(index_to_rm, 1)

            .catch (resp) !->
                $log.info "Error when trying to remove the card " + card_id

    # Set focus:
    # angular.element('#default-input').trigger('focus')

    $window.document.title = "Abelujo - " + gettext("To command")


]

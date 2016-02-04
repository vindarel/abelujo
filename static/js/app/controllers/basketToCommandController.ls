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

angular.module "abelujo" .controller 'basketToCommandController', ['$http', '$scope', '$timeout', 'utils', '$window', '$log', '$uibModal', ($http, $scope, $timeout, utils, $window, $log, $uibModal) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {find, sum, map, filter, lines, group-by} = require 'prelude-ls'

    # url encodings for "mailto"
    NEWLINE = "%0D%0A"
    ESPERLUETTE = "%26"

    AUTO_COMMAND_ID = 1
    $scope.cards = []
    $scope.sorted_cards = {}
    $scope.distributors = []
    $scope.grouped_dist = {}
    $scope.bodies = {} # pub_id, email body

    $http.get "/api/baskets/#{AUTO_COMMAND_ID}",
    .then (response) ->
        $scope.cards = response.data
        $scope.sorted_cards = group-by (.distributor.id), $scope.cards

    $http.get "/api/distributors",
    .then (response) !->
        $scope.distributors = response.data
        $scope.grouped_dist = group-by (.id), $scope.distributors

    $scope.get_body = (pub_id) ->
        "Get the list of cards and their quantities for the email body.
        "
        cards = $scope.sorted_cards[pub_id]
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
        pub = find (.id == parseInt(pub_id, 10)), $scope.distributors
        discount = pub.discount
        total_discount = total_price - total_price * discount / 100

        body = body.replace "&", ESPERLUETTE # beware other encoding pbs
        body += NEWLINE + gettext("total price: ") + total_price + " €"
        body += NEWLINE + gettext("total with {}% discount: ").replace("{}", discount) + total_discount + " €"
        body += NEWLINE + gettext("Thank you.")
        $scope.bodies[pub_id] = body
        body

    # Set focus:
    # angular.element('#default-input').trigger('focus')

    $window.document.title = "Abelujo - " + gettext("To command")


    $scope.open = (size) !->
        modalInstance = $uibModal.open do
            animation: $scope.animationsEnabled
            templateUrl: 'commandModal.html'
            controller: 'CommandModalControllerInstance'
            ## backdrop: 'static'
            size: size,
            resolve: do
                cards: ->
                    $scope.cards
                utils: ->
                    utils

        modalInstance.result.then (selectedItem) !->
            $scope.selected = selectedItem
        , !->
              $log.info "modal dismissed"

]

# We'll use this modal shortly !
angular.module "abelujo" .controller "CommandModalControllerInstance", ($http, $scope, $uibModalInstance, $window, $log, cards, utils) ->

    {group-by} = require 'prelude-ls'

    $scope.cards = cards
    $scope.sorted_cards = group-by (.distributor.id), $scope.cards

    $scope.ok = ->
        $modalInstance.close()
        $log.info "post new inventory !"

          #  This is needed for Django to process the params to its
          #  request.POST dictionnary:
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

          #  We need not to pass the parameters encoded as json to Django.
          #  Encode them like url parameters.
        $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.
        config = do
              headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        params = do
            "place_id": $scope.place.id
        $http.post "/api/inventories/create", params
        .then (response) !->
            $scope.inventory = response.data.data.inventory_id

            if $scope.inventory
                #XXX localization: en, fr,...
                $window.location.href = "/en/inventories/#{$scope.inventory}/"
            #else: display error.

    $scope.cancel = !->
        $modalInstance.dismiss('cancel')

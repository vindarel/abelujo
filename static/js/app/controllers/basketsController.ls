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

angular.module "abelujo" .controller 'basketsController', ['$http', '$scope', '$timeout', '$filter', '$window', '$uibModal', '$log', 'utils', ($http, $scope, $timeout, $filter, $window, $uibModal, $log, utils) !->

    $scope.baskets = []
    $scope.copies = []
    $scope.alerts = []
    $scope.show_buttons = {}
    $scope.new_name = null

    $http.get "/api/baskets"
    .then (response) ->
        response.data.data.map (item) !->
            $scope.baskets.push item
            if $scope.baskets[0].id
                $scope.showBasket 0

    $scope.showBasket = (item) !->
        $scope.cur_basket = $scope.baskets[item]
        if not $scope.cur_basket.copies
            $http.get "/api/baskets/#{$scope.cur_basket.id}/copies"
            .then (response) !->
                $scope.baskets[item].copies = response.data.data
                $scope.copies = response.data.data

        else
            $scope.copies = $scope.cur_basket.copies

    $window.document.title = "Abelujo - " + gettext("Baskets")

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1


    $scope.remove_from_selection = (index_to_rm) !->
        "Remove the card from the list. Server call to the api."
        sure = confirm(gettext("Are you sure to remove the card '{}' from the basket ?").replace("{}", $scope.copies[index_to_rm].title))
        if sure
            card_id = $scope.copies[index_to_rm].id
            $http.post "/api/baskets/#{$scope.cur_basket.id}/remove/#{card_id}/",
            .then (response) !->
                $scope.copies.splice(index_to_rm, 1)
                $scope.alerts = response.data.msgs

            .catch (resp) !->
                $log.info "Error when trying to remove the card " + card_id

    $scope.open = (size) !->
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
        , !->
              $log.info "modal dismissed"


]

angular.module "abelujo" .controller "BasketModalControllerInstance", ($http, $scope, $uibModalInstance, $window, $log, utils) ->

    $scope.ok = !->
        $log.info "create new basket !"

        #  This is needed for Django to process the params to its
        #  request.POST dictionnary:
        $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

        #  We need not to pass the parameters encoded as json to Django.
        #  Encode them like url parameters.
        $http.defaults.transformRequest = utils.transformRequestAsFormPost # don't transfrom params to json.
        config = do
            headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        params = do
            name: $scope.new_name

        $http.post "/api/baskets/create", params
        .then (response) !->
            basket = response.data.data
            $scope.alerts = response.data.alerts
            $uibModalInstance.close(basket)


    $scope.cancel = !->
        $uibModalInstance.dismiss('cancel')

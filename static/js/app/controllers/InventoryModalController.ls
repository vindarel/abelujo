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

angular.module "abelujo" .controller "InventoryModalController", ($http, $scope, $uibModal, $log, utils) !->

    {sum, map, filter, lines, sort, sort-by} = require 'prelude-ls'

    $scope.animationsEnabled = true

    $scope.data = {}
    $scope.places = []
    $scope.place = {}
    $scope.shelfs = []
    $scope.shelf = {}
    $scope.publisher = {}
    $scope.publishers = []

    $http.get "/api/places"
        .then (response) !->
            $scope.places = response.data
            $scope.data.places = response.data

    $http.get "/api/shelfs"
        .then (response) !->
            $scope.shelfs = sort-by (.fields.name), response.data
            $scope.shelf = $scope.shelfs[0]

    $http.get "/api/publishers/"
    .then (response) !->
        $scope.publishers = sort-by (.fields.name), response.data

    $scope.open = (size) !->
        modalInstance = $uibModal.open do
            animation: $scope.animationsEnabled
            templateUrl: 'modalContent.html'
            controller: 'ModalInstanceCtrl'
            ## backdrop: 'static'
            size: size,
            resolve: do
                places: ->
                    $scope.places
                place: ->
                    $scope.place
                shelfs: ->
                    $scope.shelfs
                shelf: ->
                    $scope.shelf
                publishers: ->
                    $scope.publishers
                publisher: ->
                    $scope.publisher
                utils: ->
                    utils

        modalInstance.result.then (selectedItem) !->
            $scope.selected = selectedItem
        , !->
              $log.info "modal dismissed"


angular.module "abelujo" .controller "ModalInstanceCtrl", ($http, $scope, $uibModalInstance, places, $window, $log, place, shelfs, shelf, publishers, publisher, utils) !->

    $scope.places = places
    $scope.place = place
    $scope.shelfs = shelfs
    $scope.shelf = shelf
    $scope.publishers = publishers
    $scope.publisher = publisher
    $scope.ok = (model) ->
        $uibModalInstance.close()
        $log.info "post new inventory !"

        language = utils.url_language($window.location.pathname)

        params = do
            place_id: $scope.place.id if model == 'place'
            shelf_id: $scope.shelf.pk if model == 'shelf'
            publisher_id: $scope.publisher.pk if model == 'publisher'

        $http.post "/api/inventories/create", params
        .then (response) !->
            inventory_id = response.data.data.inventory_id

            if inventory_id
                $window.location.href = "/#{language}/inventories/#{inventory_id}/"
            #else: display error.

    $scope.cancel = !->
        $uibModalInstance.dismiss('cancel')

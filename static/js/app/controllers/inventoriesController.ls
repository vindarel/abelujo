# Copyright 2014 - 2017 The Abelujo Developers
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

angular.module "abelujo" .controller 'inventoriesController', ['$http', '$scope', '$log', 'utils', ($http, $scope, $log, utils) !->

    {sum, map, filter, lines, reverse, sort-by} = require 'prelude-ls'

    # $scope.language = utils.url_language($window.location.pathname)

    $scope.inventories = []
    $scope.alerts = []

    $http.get "/api/inventories/"
    .then (response) !->

        if response.data.status == "error"
            $log.error "Error while getting inventories server side"
        $scope.inventories = response.data.data
        # $scope.alerts = response.data.alerts

    $scope.last_sort = "name"
    $scope.sort_by = (key) !->
        if $scope.last_sort == key
            $scope.inventories = $scope.inventories
            |> reverse
        else
            $scope.inventories = $scope.inventories
            |> sort-by ( -> it[key])
            $scope.last_sort = key


    # XXX: adapted from inventoryTerminateController
    $scope.validate = (index) !->
        inv = $scope.inventories[index]
        if inv.applied
            alert gettext "This inventory is already applied."
        else
            sure = confirm gettext "Are you sure to apply this inventory to your stock ?"
            if sure
                inv.ongoing = true
                $http.post "/api/inventories/#{inv.id}/apply"
                .then (response) !->
                    status = response.data.status
                    $scope.alerts = response.data.alerts

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1

]

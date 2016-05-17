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

angular.module "abelujo" .controller 'historyController', ['$http', '$scope', '$timeout', '$filter', '$window', 'utils', '$log', 'hotkeys', ($http, $scope, $timeout, $filter, $window, utils, $log, hotkeys) !->

    {Obj, join, sum, map, filter, lines} = require 'prelude-ls'

    $scope.history = []
    $scope.to_show = []
    $scope.filterModel = 'All'
    $scope.alerts = []
    $scope.show_images = true

    params = do
        query: ""
    $http.get "/api/history", do
        params: params
    .then (response) ->
        response.data.data.map (item) !->
            repr = "item n° " + item.id
            $scope.history.push do
                id: item.id
                repr: repr
                item: item
            $scope.to_show = $scope.history
            |> filter (.item.model == 'Entry')

            return do
                repr: repr
                id: item.id

    $scope.filterHistory = (model) !->
        $log.info model
        $scope.to_show = $scope.history
        |> filter (.item.model == model)

    $scope.sellUndo = (index) !->
        sell = $scope.to_show[index]
        $log.info "undo sell #{sell.item.id}"

        sure = confirm gettext "Are you sure to undo this sell ?"
        if sure
            $http.get "/api/sell/#{sell.item.id}/undo"
            .then (response) !->
                $scope.alerts.push response.data.alerts

    $scope.closeAlert = (index) !->
        $scope.alerts.splice index, 1

    $scope.toggle_images = !->
        $scope.show_images = not $scope.show_images

    # Keyboard shortcuts (hotkeys)
    hotkeys.bindTo($scope)
    .add do
        combo: "d"
        description: gettext "show or hide the book details in tables."
        callback: !->
            $scope.toggle_images!

    $window.document.title = "Abelujo - " + gettext("History")

]

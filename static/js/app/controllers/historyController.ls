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

    {Obj, join, reject, sum, map, filter, find, lines, sort-by, find-index, reverse} = require 'prelude-ls'

    $scope.history = []
    $scope.sells_month = {}
    $scope.to_show = []
    $scope.filterModel = 'All'
    $scope.alerts = []
    $scope.show_details = 0
    $scope.show_tab = 'sells'
    $scope.last_sort = "created"

    params = do
        query: ""
    $http.get "/api/history/sells", do
        params: params
    .then (response) ->
        response.data.data.map (item) !->
            repr = "sell n° " + item.id
            created = Date.parse(item.created)
            created = created.toString("d-MMM-yyyy") # human representation
            item.created = created
            $scope.history.push do
                id: item.id
                repr: repr
                item: item
                show_row: false
                show_covers: false
            $scope.to_show = $scope.history
            $scope.sells = $scope.history
            # |> filter (.item.model == 'Entry')

            return do
                repr: repr
                id: item.id

    $http.get "/api/stats/sells/month"
    .then (response) !->
        $scope.sells_month = response.data

    $scope.history_entries = !->
        $http.get "/api/history/entries"
        .then (response) !->
            $scope.show_tab = 'entries'
            $scope.entries = response.data.data
            |> map (-> it.created = Date.parse(it.created).toString("d-MMM-yyyy"); it)
            $log.info response.data

    $scope.select_tab = (model) !->
        $scope.show_tab = model

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

    $scope.toggle_details = !->
        "0: show nothing, 1: show second tables, 2: show also covers"
        $scope.show_details +=  1
        if $scope.show_details == 3
            $scope.show_details = 0

    $scope.sort_by = (key) ->
        """Custom sort function. Smart-table is buggy and
        under-documented. Didn't find a good table for angular.
        """
        if $scope.last_sort == key
            $scope.sells = $scope.sells
            |> reverse
        else
            $scope.sells = $scope.sells
            |> sort-by ( -> it.item[key])
            $scope.last_sort = key

        $log.info $scope.sells

    # Keyboard shortcuts (hotkeys)
    hotkeys.bindTo($scope)
    .add do
        combo: "d"
        description: gettext "show or hide the book details in tables."
        callback: !->
            $scope.toggle_details!

    $window.document.title = "Abelujo - " + gettext("History")

]

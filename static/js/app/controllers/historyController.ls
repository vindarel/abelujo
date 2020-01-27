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

angular.module "abelujo" .controller 'historyController', ['$http', '$scope', '$timeout', '$filter', '$window', 'utils', '$log', 'hotkeys', '$resource', 'tmhDynamicLocale', ($http, $scope, $timeout, $filter, $window, utils, $log, hotkeys, $resource, tmhDynamicLocale) !->

    {Obj, join, reject, sum, map, filter, find, lines, sort-by, find-index, reverse, take, group-by, unique-by} = require 'prelude-ls'

    $scope.history = []
    $scope.sells_month = 0.0  # total revenue of sold cards. Float.
    $scope.total_sells_month_excl_tax = 0.0  # same total, minus the vat.
    $scope.back = []
    $scope.filterModel = 'All'
    $scope.alerts = []
    $scope.show_details = false
    $scope.show_unique= false
    $scope.show_tab = 'sells'
    $scope.last_sort = "created"

    $scope.today = ->
        $scope.user_date = new Date()

    $scope.user_date = $scope.today!

    $scope.page = 1
    $scope.page_size = 15
    $scope.page_max = 1
    $scope.sortorder = 0  # ascending/descending. 0: default, 1 other.
    $scope.sortby = ""    # sort key (created, title etc)
    # $scope.cache_per_month_per_page = {}  # key: month -> dict with key: page

    $scope.get_history = !->
        params = do
            month: $scope.user_date.getMonth! + 1
            year: $scope.user_date.getFullYear!
            page: $scope.page
            page_size: $scope.page_size
            sortby: $scope.sortby
            sortorder: $scope.sortorder
        $http.get "/api/history/sells", do
            params: params
        .then (response) ->
            $scope.sells = []
            $scope.sells_month = 0
            $scope.total_sells_month_excl_tax = 0
            $scope.nb_sells = response.data.data.nb_sells
            $scope.nb_cards_sold = response.data.data.nb_cards_sold
            $scope.get_page_max response.data.data.total
            # $scope.best_sells = utils.best_sells response.data.data
            # $scope.sells_mean = utils.sells_mean response.data.data

            response.data.data.data.map (item) !->
                repr = "sell n° " + item.id
                created = Date.parse(item.created)
                created = created.toString("d-MMM-yyyy") # human representation
                item.created = created
                item.repr = repr
                item.show_row = false
                item.show_covers = false
                $scope.sells.push item

                $scope.sells_month += item.price_sold
                $scope.total_sells_month_excl_tax += item.price_sold_excl_tax

                return do
                    repr: repr
                    id: item.id

    $scope.get_history!

    $scope.get_page_max = ! ->
        # Get the nb of pages. 16 elements / 3 elts per page = 5.xx, 16%3 = 1 --> 6 pages.
        add_one_page = (total, page_size) ->
            if (total % page_size == 0)
                return 0
            return 1

        $scope.page_max = Math.floor($scope.nb_sells / this.page_size) + add_one_page($scope.nb_sells, $scope.page_size)

    $scope.nextPage = !->
        if $scope.page < $scope.page_max
            $scope.page += 1
            $scope.get_history!

    $scope.previousPage = !->
        if $scope.page > 1
            $scope.page -= 1
            $scope.get_history!

    $scope.firstPage = !->
        $scope.page = 1
        $scope.get_history!

    $scope.lastPage = !->
        $scope.page = $scope.page_max
        $scope.get_history!


    # Get stats.
    $scope.get_stats = !->
        stats_params = do
            year: $scope.user_date.getFullYear!
            month: $scope.user_date.getMonth! + 1
        $http.get "/api/stats/sells/month", do
            params: stats_params
        .then (response) !->
            $scope.stats_month = response.data
    $scope.get_stats!


    $scope.history_entries = !->
        $http.get "/api/history/entries"
        .then (response) !->
            $scope.show_tab = 'entries'
            $scope.entries = response.data.data
            |> map (-> it.created = Date.parse(it.created).toString("d-MMM-yyyy"); it)
            $log.info response.data

        $http.get "/api/stats/entries/month"
        .then (response) !->
            $scope.entries_month = response.data

    $scope.select_tab = (model) !->
        $scope.show_tab = model

    $scope.sellUndo = (index) !->
        sell = $scope.sells[index]
        $log.info "undo sell #{sell.id}"

        sure = confirm gettext "Are you sure to undo this sell ?"
        if sure
            params = do
                soldcard_id: sell.soldcard_id
            $http.get "/api/sell/#{sell.sell_id}/undo", do
                params: params
            .then (response) !->
                $scope.alerts = response.data.alerts

    $scope.closeAlert = (index) !->
        $scope.alerts.splice index, 1

    $scope.toggle_details = !->
        $scope.show_details = not $scope.show_details

    $scope.sort_by = (key) ->
        """Custom sort function. Smart-table is buggy and
        under-documented. Didn't find a good table for angular.
        """
        $scope.sortby = key
        $scope.sortorder = ($scope.sortorder + 1) % 2
        $scope.get_history!


    # Keyboard shortcuts (hotkeys)
    hotkeys.bindTo($scope)
    .add do
        combo: "d"
        description: gettext "show or hide the book details in tables."
        callback: !->
            $scope.toggle_details!

    .add do
        combo: "f"
        description: gettext "filter one title per line"
        callback: !->
            $scope.show_unique = not $scope.show_unique
            $scope.filter_unique!

    ######################################################
    # Month picker
    ######################################################

    $scope.getMonth = ->
        if $scope.user_date
            $scope.user_date.getMonth! + 1

    $scope.user_popup_status = do
        opened: false

    $scope.user_open_datepicker = (event) ->
        $scope.user_popup_status.opened = true

    $scope.datepicker_user_options = do
        minMode: "month"
        formatYear: 'yyyy'
        formatMonth: 'MMMM'
        startingDay: 1

    $scope.user_date_format = "MMMM"

    $scope.user_change_month = !->
        # if not date in future
        $scope.get_history!
        $scope.get_stats!

    $window.document.title = "Abelujo - " + gettext("History")

]

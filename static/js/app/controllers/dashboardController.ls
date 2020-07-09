# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

angular.module "abelujo" .controller 'dashboardController', ['$http', '$scope', '$timeout', '$window', '$log', 'utils', '$locale', 'tmhDynamicLocale', ($http, $scope, $timeout, $window, $log, utils, $locale, tmhDynamicLocale) !->

    {sum, map, filter, lines} = require 'prelude-ls'

    $scope.language = utils.url_language($window.location.pathname)
    # $locale.id can not be set, we have to use another plugin.
    tmhDynamicLocale.set($scope.language) # mmh...

    $scope.stats = undefined
    $scope.sells_month = {}     # Keys are different stats: "best_sells" is a list, etc.

    params = do
        language: $scope.language

    $http.get "/api/stats/", do
        params: params
    .then (response) !->
        response.data.data
        $scope.stats = response.data

    $scope.shelfs = []
    $scope.shelf = {}


    $http.get "/api/stats/sells/month"
    .then (response) !->
        $scope.sells_month = response.data

    # xxx: deposits' due dates
    ## $http.get "/api/deposits/due_dates/"
    ## .then (response) !->
        ## $scope.deposits = response.data

    ######################################################
    # Month picker for the monthly revenue
    ######################################################
    $scope.revenue_date = undefined


    $scope.today = ->
        $scope.revenue_date = new Date()
    $scope.today!

    $scope.revenue_popup_status = do
        opened: false

    $scope.revenue_open_datepicker = (event) ->
        $scope.revenue_popup_status.opened = true

    $scope.datepicker_revenue_options = do
        minMode: "month"
        formatYear: 'yyyy'
        formatMonth: 'MMMM'
        startingDay: 1

    $scope.revenue_date_format = "MMMM"

    $scope.revenue_change_month = !->
        # if not date in future
        params = do
            year: $scope.revenue_date.getFullYear!
            month: $scope.revenue_date.getMonth! + 1
        $log.info "Calling monthly report for " + $scope.revenue_date
        $http.get "/api/stats/sells/month", do
            params: params
        .then (response) !->
            $scope.sells_month = response.data

    $window.document.title = "Abelujo" + " - " + gettext "dashboard"

]

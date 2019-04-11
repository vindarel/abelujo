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

angular.module "abelujo" .controller 'dashboardController', ['$http', '$scope', '$timeout', '$window', '$log', 'utils', '$locale', 'tmhDynamicLocale', ($http, $scope, $timeout, $window, $log, utils, $locale, tmhDynamicLocale) !->

    {sum, map, filter, lines} = require 'prelude-ls'

    $scope.language = utils.url_language($window.location.pathname)
    # $locale.id can not be set, we have to use another plugin.
    tmhDynamicLocale.set($scope.language) # mmh...

    $scope.stats = undefined
    $scope.sells_month = {}     # Keys are different stats: "best_sells" is a list, etc.
    $scope.stock_age_cards = [] # list of cards

    params = do
        language: $scope.language

    $http.get "/api/stats/", do
        params: params
    .then (response) !->
        response.data.data
        $scope.stats = response.data

        chart = c3.generate do
            bindto: \#chart
            data: do
                type: "pie"
                columns: [
                    [$scope.stats.nb_titles.label, $scope.stats.nb_titles.value]
                    [$scope.stats.nb_unknown.label, $scope.stats.nb_unknown.value]
                ]


        chart2 = c3.generate do
            bindto: \#chart2
            data: do
                type: "pie"
                columns: [
                    [$scope.stats.total_cost.label, $scope.stats.total_cost.value]
                    [$scope.stats.deposits_cost.label, $scope.stats.deposits_cost.value]
                ]
            color: do
                pattern: ['#0000cd', '#ffd700']

        chart-no-stock = c3.generate do
            bindto: \#chartNoStock
            data: do
                type: "pie"
                columns: [
                    [$scope.stats.nb_cards_no_stock.label, $scope.stats.nb_cards_no_stock.value]
                    [$scope.stats.nb_cards_one_copy.label, $scope.stats.nb_cards_one_copy.value]
                    [$scope.stats.nb_titles.label, $scope.stats.nb_titles.value]
                ]
            color: do
                pattern: ['#ff8c00', '#ffd700', '#6495ed']


    $scope.shelfs = []
    $scope.shelf = {}

    $scope.age_shelf = !->
      """
      """

      if $scope.shelfs
          params = do
              shelf_id: $scope.shelf.pk

          $http.get "/api/stats/stock_age/", do
              params: params

          .then (response) !->
              data = response.data
              if data
                  $log.info "Building the age shelf graph with new data"
                  chart-age = c3.generate do
                    bindto: \#chart-age
                    data: do
                        type: "pie"
                        columns: [
                            [gettext("3 months"), data["0"].length],
                            [gettext("6 months"), data["1"].length],
                            [gettext("12 months"), data["2"].length],
                            [gettext("18 months"), data["3"].length],
                            [gettext("24 months"), data["4"].length],
                            [gettext("more than 24 months"), data["5"].length],
                        ]
                        onclick: (d, i) !->
                            # d: data, i: chart info
                            $log.info "onclick", d, i
                            $log.info data[d.index]
                            $scope.stock_age_cards = data[d.index]
                            $log.info $scope.stock_age_cards
                            $scope.$apply! # otherwise the scope doesn't refresh

                    color: do
                        pattern: ['#077efa', '#07fac9', '#cdfa07', '#faea07', '#fa6507', '#fa0c07']

    getShelfs = ->
      utils.shelfs!
      .then (response) ->
          $scope.shelfs = response.data
          if $scope.shelfs.length
              $scope.shelf = $scope.shelfs[0]
              $scope.age_shelf!
    getShelfs!

    $http.get "/api/stats/sells/month"
    .then (response) !->
        $scope.sells_month = response.data

    $http.get "/api/stats/static"
    .then (response) !->
        $scope.static_stock = response.data

    $http.get "/api/deposits/due_dates/"
    .then (response) !->
        $scope.deposits = response.data

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

    #
    # Instance the tour
    #
    tour = new Tour do
      # storage: false  # for dev
      steps:
          * element: "\#mystock",
            title: gettext "Welcome to Abelujo !",
            content: gettext "The interesting stuff will happen in these menus ! Remember that we have  documentation on our website."
          * element: "\#database"
            title: gettext "Fine grain database"
            content: gettext "This menu is to fine tune the content of your database. You shouldn't need to look at it yet."
            placement: "bottom"
          * element: "\#titlesearch"
            title: gettext "Quick navigation"
            content: gettext "This little box is to quickly go to the card of a title you have in stock. Type a few letters, press Enter and see the bibliographic and stock information. \n Enjoy !"
            placement: "bottom"

    # Initialize the tour
    tour.init()

    # Start the tour
    tour.start()

    $window.document.title = "Abelujo" + " - " + gettext "dashboard"

]

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

angular.module "abelujo" .controller 'dashboardController', ['$http', '$scope', '$timeout', '$window', '$log', 'utils', ($http, $scope, $timeout, $window, $log, utils) !->

    {sum, map, filter, lines} = require 'prelude-ls'

    $scope.stats = undefined
    $scope.sells_month = {}
    $scope.stock_age_cards = [] # list of cards

    $http.get "/api/stats/"
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

          $log.info params
          $http.get "/api/stats/stock_age/", do
              params: params

          .then (response) !->
              data = response.data
              if data
                  $log.info "shelf data:"
                  $log.info data
                  chart-age = c3.generate do
                    bindto: \#chart-age
                    data: do
                        type: "pie"
                        columns: [
                            ["3 months", data["0"].length],
                            ["6 months", data["1"].length],
                            ["12 months", data["2"].length],
                            ["18 months", data["3"].length],
                            ["24 months", data["4"].length],
                            ["more than 24 months", data["5"].length],
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

    $window.document.title = "Abelujo" + " - " + gettext "dashboard"

]

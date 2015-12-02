angular.module "abelujo" .controller 'dashboardController', ['$http', '$scope', '$timeout', ($http, $scope, $timeout) !->

    {sum, map, filter, lines} = require 'prelude-ls'

    $scope.stats = undefined

    $http.get "/api/stats/"
    .then (response) !->
        response.data.data
        $scope.stats = response.data

        chart = c3.generate do
            bindto: \#chart
            data: do
                type: "pie"
                columns: [
                    [$scope.stats.nb_books.label, $scope.stats.nb_books.value]
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
                    [$scope.stats.nb_books.label, $scope.stats.nb_books.value]
                ]
            color: do
                pattern: ['#ff8c00', '#ffd700', '#6495ed']


]

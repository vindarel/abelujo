angular.module "abelujo" .controller 'historyController', ['$http', '$scope', '$timeout', '$filter', '$window', 'utils', ($http, $scope, $timeout, $filter, $window, utils) !->

    $scope.history = []
    $scope.filterModel = 'All'
    $scope.alerts = []

    params = do
        query: null
    $http.get "/api/history", params
    .then (response) ->
        response.data.data.map (item) !->
            repr = "item n° " + item.id
            $scope.history.push do
                id: item.id
                repr: repr
                item: item
            return do
                repr: repr
                id: item.id

    $scope.showModel = (model) !->
        if (model == $scope.filterModel) or ($scope.filterModel == 'All')
            return true
        return false

    $scope.sellUndo = (index) !->
        sell = $scope.history[index]

        $http.get "/api/sell/#{sell.item.id}/undo"
        .then (response) !->
            $scope.alerts.push response.data.alerts

    $scope.closeAlert = (index) !->
        $scope.alerts.splice index, 1

    $window.document.title = "Abelujo - " + gettext("History")

]

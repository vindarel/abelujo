angular.module "abelujo" .controller 'historyController', ['$http', '$scope', '$timeout', '$filter', ($http, $scope, $timeout, $filter) !->

    $scope.history = []
    $scope.filterModel = 'All'

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


]

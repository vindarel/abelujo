angular.module "abelujo" .controller 'basketsController', ['$http', '$scope', '$timeout', '$filter', '$window', ($http, $scope, $timeout, $filter, $window) !->

    $scope.baskets = []
    $scope.copies = []

    $http.get "/api/baskets"
    .then (response) ->
        response.data.data.map (item) !->
            $scope.baskets.push item
            if $scope.baskets[0].id
                $scope.showBasket 0

    $scope.showBasket = (item) !->
        cur = $scope.baskets[item]
        if not cur.copies
            $http.get "/api/baskets/#{cur.id}/copies"
            .then (response) !->
                $scope.baskets[item].copies = response.data.data
                $scope.copies = response.data.data

        else
            $scope.copies = cur.copies

    $window.document.title = "Abelujo - " + gettext("Baskets")

]

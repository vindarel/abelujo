angular.module("abelujo").controller('alertsController', ['$http', '$scope', '$timeout', 'utils', '$filter', function ($http, $scope, $timeout, utils, $filter) {
    // utils: in services.js

    $http.get("/api/alerts")
        .then(function(response){
            $scope.alerts = response.data.data;
            return response.data.data;
        });

  }]);

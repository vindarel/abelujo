angular.module("abelujo").controller('baseController', ['$http', '$scope', '$timeout', 'utils', '$filter', function ($http, $scope, $timeout, utils, $filter) {
    // utils: in services.js
    $scope.alerts_open = null;
    $scope.auto_command_total = null;

    $http.get("/api/alerts/open")
        .then(function(response){
            $scope.alerts_open = response.data;
            return response.data.data;
        });

    $http.get("/api/baskets/auto_command/open")
        .then(function(response){
            $scope.auto_command_total = response.data;
            return response.data.data;
        });
  }]);

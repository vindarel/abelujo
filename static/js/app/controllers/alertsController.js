angular.module("abelujo").controller('alertsController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', function ($http, $scope, $timeout, utils, $filter, $window) {
    // utils: in services.js

    $http.get("/api/alerts")
        .then(function(response){
            $scope.alerts = response.data.data;
            return response.data.data;
        });

    $scope.print_ambiguous = function(i) {
        if ($scope.alerts[i].card.ambiguous_sell === false) {
            return gettext("not any more");
        }
        return gettext("yes");
    };

    $window.document.title = "Abelujo - " + gettext("Alerts");

  }]);

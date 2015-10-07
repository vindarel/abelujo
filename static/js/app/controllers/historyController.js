angular.module("abelujo").controller('historyController', ['$http', '$scope', '$timeout', 'utils', '$filter', function ($http, $scope, $timeout, utils, $filter) {
    // utils: in services.js

    // set the xsrf token via cookies.
    // $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    $scope.history = [];
    $scope.filterModel = 'All';

    $http.get("/api/history", {
        params: {
            "query": null
        }})
        .then(function(response){ // "then", not "success"

            return response.data.data.map(function(item){
                // give a string representation for each object (result)
                // xxx: take the repr from django
                // return item.title + ", " + item.authors + ", éd. " + item.publishers;
                var repr = "item n° " + item.id;
                $scope.history.push({"id": item.id,
                                     "repr": repr,
                                     "item": item});
                return {"repr": repr, "id": item.id};
            });
        });

    $scope.showModel = function(model) {
        if ((model === $scope.filterModel) || ($scope.filterModel === "All")) {
            return true;
        }

        return false;
    };

}]);

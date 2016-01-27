angular.module "abelujo" .controller 'basketToCommandController', ['$http', '$scope', '$timeout', 'utils', '$window', ($http, $scope, $timeout, utils, $window) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines} = require 'prelude-ls'

    AUTO_COMMAND_ID = 1
    $scope.cards = []

    $http.get "/api/baskets/#{AUTO_COMMAND_ID}",
    .then (response) ->
        $scope.cards = response.data

    # Set focus:
    # angular.element('#default-input').trigger('focus')

    $window.document.title = "Abelujo - " + gettext("To command")

]

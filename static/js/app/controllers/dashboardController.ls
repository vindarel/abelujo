angular.module "abelujo" .controller 'dashboardController', ['$http', '$scope', '$timeout', 'utils', '$filter', '$window', ($http, $scope, $timeout, utils, $filter, $window) !->
    # utils: in services.js

    # set the xsrf token via cookies.
    # $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    {sum, map, filter, lines} = require 'prelude-ls'



    chart = c3.generate do
        bindto: \#chart
        data: do
            type: "pie"
            columns: [
                ['data1', 10]
                ['data2', 40]
            ]


    chart2 = c3.generate do
        bindto: \#chart2
        data: do
            type: "pie"
            columns: [
                ['data1', 223]
                ['data2', 618]
            ]
        color: do
             pattern: ['#0000cd', '#ffd700']

]

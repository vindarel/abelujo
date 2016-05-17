# Copyright 2014 - 2016 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

angular.module "abelujo" .controller 'baseController', ['$http', '$scope', '$window', 'utils', ($http, $scope, $window, utils) !->

    {Obj, join, reject, sum, map, filter, lines} = require 'prelude-ls'


    $scope.alerts_open = null
    $scope.auto_command_total = null

    $http.get("/api/alerts/open")
        .then (response) ->
            $scope.alerts_open = response.data
            return response.data.data

    $http.get("/api/baskets/auto_command/open")
        .then (response) ->
            $scope.auto_command_total = response.data
            return response.data.data

    # Goal: Grab what url we're on to highlight the active menu bar,
    # with ng-class.
    $scope.url = ""
    path = $window.location.pathname

    re = RegExp "\/([a-z][a-z])\/\([a-z]+\)/?"
    res = path.match re
    if res
        $scope.url = res[* - 1] # *: last

]
